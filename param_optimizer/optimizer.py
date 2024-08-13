import psycopg2
import jax.numpy as jnp
import jax
import numpy as np
import pandas as pd
import numpyro
import numpyro.distributions as dist
from jax import random
from numpyro.infer import MCMC, NUTS
import time
from jax import lax

"""Can get trades data from : https://public.bybit.com/trading/ 
So the optimizer is set up using the trades data with 
simulated prices to find the optimal kappa(decay) 
based on the various holding periods of interest.


The idea around using simulated prices is that if historical prices were used, 
the optimal kappa (decay parameter) might be biased towards that specific market reality. 
By using simulated prices instead,the optimizer can find the optimal kappa values based on a random universe of price movements with characteristics and properties similar to crypto coins.
"""


trade_df = df.copy()


trade_df['side'] = np.where(trade_df['side'] == 'BUY', 1, -1)


trade_df = trade_df.drop('exchange', axis=1)

trade_df_filtered = trade_df[['quantity', 'side', 'price']]

# price_data = trade_df['price'].astype(float)

# Parameters for price simulation
nsim = 100 # number of simulations
t = 100 * 24 * 60  # 100 days in minutes
mu = -1 / (24 * 60)  # Drift rate adjusted for minute intervals
sigma = 1.5 / np.sqrt(24 * 60)  # Volatility adjusted for minute intervals
S0 = 100
phi = 0.1
lambda_jump = 0.2
mu_j = 0
sigma_j = 1

np.random.seed(503)

def generate_ar1_with_jumps(nsim, t, phi, lambda_jump, mu_j, sigma_j):
    epsilon = np.zeros((t, nsim))

    epsilon[0, :] = np.random.normal(0, 1, nsim)

    for i in range(1, t):
        eta = np.random.normal(0, 1, nsim)
        epsilon[i, :] = phi * epsilon[i-1, :] + eta
        jump_mask = np.random.uniform(0, 1, nsim) < lambda_jump
        jump_sizes = np.random.normal(mu_j, sigma_j, nsim) * jump_mask
        epsilon[i, :] += jump_sizes

    return epsilon

def gbm_autocor_jumps(nsim, t, mu, sigma, S0, phi, lambda_jump, mu_j, sigma_j):
    dt = 1 / (365 * 24 * 60)
    epsilon = generate_ar1_with_jumps(nsim, t, phi, lambda_jump, mu_j, sigma_j)
    gbm = np.exp((mu - sigma**2 / 2) * dt + sigma * epsilon * np.sqrt(dt))
    gbm = np.vstack([np.full(nsim, S0), gbm])
    gbm = np.cumprod(gbm, axis=0)

    return gbm


simulated_prices = gbm_autocor_jumps(nsim, t, mu, sigma, S0, phi, lambda_jump, mu_j, sigma_j)

if simulated_prices.size == 0:
    print("Simulation returned empty data. Check the simulation function.")
else:
    print(f"Simulation returned data with shape {simulated_prices.shape}.")

class TradingStrategy:
    def __init__(self, kappa, threshold):
        self.kappa = kappa
        self.threshold = threshold

    def compute_BSI(self, quantities, sides, kappa):
        decay = jnp.exp(-kappa)

        BSI_values = jnp.zeros_like(quantities, dtype=float)
        BSI = 0
        for i in range(len(quantities)):
            BSI = BSI * decay + (quantities[i] * sides[i])
            BSI_values = BSI_values.at[i].set(BSI)
        return BSI_values

    def generate_signals(self, BSI_values, threshold):
        signals = jnp.where(BSI_values > threshold, 1, jnp.where(BSI_values < -threshold, -1, 0))
        return signals

    def profitability(self, signals, prices, transaction_cost=0.0005):
        min_length = min(len(signals), len(prices))
        signals = signals[:min_length]
        prices = prices[:min_length]

        def step_fn(carry, inputs):
            position, profit = carry
            signal, price = inputs

            def update_position(pos_profit, entry_price):
                pos, profit = pos_profit
                new_profit = profit + (entry_price - price) * jnp.where(pos == -1, 1, -1)
                new_profit -= transaction_cost * entry_price
                return signal, new_profit

            new_position, new_profit = lax.cond(signal != 0,
                                                update_position,
                                                lambda x, y: (position, profit),
                                                (position, profit),
                                                price)

            return (new_position, new_profit), None

        init_carry = (0, 0.0)  # (position, profit)
        (final_position, final_profit), _ = jax.lax.scan(step_fn, init_carry, (signals, prices))

        return final_profit

class ParameterOptimizer:
    def __init__(self, trade_df, model_class, simulated_series):
        self.trade_df = trade_df
        self.model_class = model_class
        self.simulated_series = simulated_series
        self.holding_periods = ['5min', '10min', '15min', '30min', '1H']

    def trading_model(self, prices, quantities, sides):
        kappa = numpyro.sample('kappa', dist.Uniform(0.001, .10))
        profit = self.model(prices, quantities, sides, kappa, 1)
        return numpyro.sample('profit', dist.Normal(profit, 1.0))

    def model(self, prices, quantities, sides, kappa, threshold):
        model_instance = self.model_class(kappa, threshold)
        BSI_values = model_instance.compute_BSI(quantities, sides, kappa)
        signals = model_instance.generate_signals(BSI_values, threshold)
        profit = model_instance.profitability(signals, prices)
        return profit

    def optimize_parameters(self):
        results = {}
        for interval in self.holding_periods:
            print(f"Starting optimization for holding period: {interval}")
            start_time = time.time()

            # Reduce the size of the dataset for testing
            all_prices = jnp.concatenate([jnp.array(series) for series in self.simulated_series])[:10000]
            all_trades_quantity = jnp.array(self.trade_df['quantity'].values)[:10000]
            all_trades_side = jnp.array(self.trade_df['side'].values)[:10000]

            nuts_kernel = NUTS(self.trading_model)
            mcmc = MCMC(nuts_kernel, num_warmup=100, num_samples=100, num_chains=2)
            rng_key = random.PRNGKey(0)
            mcmc.run(rng_key, all_prices, all_trades_quantity, all_trades_side)
            mcmc.print_summary()
            samples = mcmc.get_samples()

            elapsed_time = time.time() - start_time
            print(f"Finished optimization for holding period: {interval} in {elapsed_time:.2f} seconds")
            results[interval] = samples

        return results


optimizer = ParameterOptimizer(trade_df_filtered, TradingStrategy, simulated_prices)
results = optimizer.optimize_parameters()

print("Optimization Results:")
for interval, samples in results.items():
    print(f"Interval: {interval}")
    print(samples)
