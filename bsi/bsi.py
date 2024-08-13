import numpy as np
import logging


class BSICalculator:
    def __init__(self, coin_base="BTC", warmup_period=100):
        self.coin_base = coin_base
        self.BSI = 0.0
        self.warmup_period = warmup_period
        self.trade_buffer = []

    async def process_data(self, exchange, processed_data):
        logging.info(f"Processed data from {exchange}: {processed_data}")

        if len(self.trade_buffer) < self.warmup_period:
            self.trade_buffer.append(processed_data)
            if len(self.trade_buffer) == self.warmup_period:
                logging.info("Warm-up period complete. Starting signal generation.")
        else:
            BSI_values = self.compute_BSI([processed_data])
            signals = self.generate_signals(BSI_values)

            self.handle_signals(signals)

    # current kappa for the bot kappa=0.00012
    def compute_BSI(self, trades, kappa=0.008):
        decay = np.exp(-kappa)
        BSI_values = []
        for trade in trades:
            volume = float(trade['quantity'])
            side = 1 if trade['side'] == 'buy' else -1
            self.BSI = self.BSI * decay + (volume * side)
            BSI_values.append(self.BSI)
        return BSI_values

    def generate_signals(self, BSI_values, threshold=1):
        signals = []
        for BSI in BSI_values:
            if BSI > threshold:
                signals.append(1)
                logging.info(f"Signal: 1 (Long) | BSI: {BSI}")
            elif BSI < -threshold:
                logging.info(f"Signal: -1 (Short) | BSI: {BSI}")
                signals.append(-1)
            else:
                signals.append(0)
        return signals

    def handle_signals(self, signals):
        for signal in signals:
            if signal == 1:
                logging.info("Generating long signal")
            elif signal == -1:
                logging.info("Generating short signal")
            else:
                logging.info("No signal")


