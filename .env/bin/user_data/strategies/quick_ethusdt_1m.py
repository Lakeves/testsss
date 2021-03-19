# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from talib._ta_lib import ULTOSC, MACD, SAR, LINEARREG_ANGLE, TEMA, STOCHRSI, STOCH, STOCHF, RSI

from freqtrade.strategy.interface import IStrategy

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# This class is a sample. Feel free to customize it.
class quick_ethusdt_1m(IStrategy):
    """
    This is a sample strategy to inspire you.
    More information in https://github.com/freqtrade/freqtrade/blob/develop/docs/bot-optimization.md

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the prototype for the methods: minimal_roi, stoploss, populate_indicators, populate_buy_trend,
    populate_sell_trend, hyperopt_space, buy_strategy_generator
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 1

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        "0": 0.07186329732926479,
        "6": 0.03610260437996321,
        "14": 0.014117594921808408,
        "23": 0
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.073946396013718

    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.11645094244761
    trailing_stop_positive_offset = 0.20201226976340847
    trailing_only_offset_is_reached = True

    # Optimal ticker interval for the strategy.
    timeframe = '1m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = True
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Optional order type mapping.
    order_types = {
        'buy': 'market',
        'sell': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    plot_config = {
        'main_plot': {
            'close': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "OU": {
                'ou': {'color': 'red'},
            }
        }
    }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return [("ETH/USDT", "1m")]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame
        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        # MACD
        dataframe['macd'], dataframe['macdsignal'], dataframe['macdhist'] = MACD(dataframe['close'], fastperiod=12,
                                                                                 slowperiod=26, signalperiod=9)
        dataframe['macd_angle'] = LINEARREG_ANGLE(dataframe['macd'], timeperiod=3)
        dataframe['macdhist_angle'] = LINEARREG_ANGLE(dataframe['macd'], timeperiod=3)

        # Linear angle 
        dataframe['angle'] = LINEARREG_ANGLE(dataframe['close'], timeperiod=14)

        dataframe['tema'] = TEMA(dataframe['close'], timeperiod=30)
        dataframe['sr_fastk'], dataframe['sr_fastd'] = STOCHRSI(dataframe['close'], timeperiod=14, fastk_period=5,
                                                                fastd_period=3, fastd_matype=0)
        dataframe['sr_fastd_angle'] = LINEARREG_ANGLE(dataframe['sr_fastd'], timeperiod=4)

        dataframe['slowk'], dataframe['slowd'] = STOCH(dataframe['high'], dataframe['low'], dataframe['close'],
                                                       fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3,
                                                       slowd_matype=0)
        dataframe['slowd_angle'] = LINEARREG_ANGLE(dataframe['slowd'], timeperiod=3)
        dataframe['sf_fastk'], dataframe['sf_fastd'] = STOCHF(dataframe['high'], dataframe['low'], dataframe['close'], fastk_period=5, fastd_period=3, fastd_matype=0)
        dataframe['sf_fastd_angle'] = LINEARREG_ANGLE(dataframe['sf_fastd'], timeperiod=3)

        dataframe['rsi'] = RSI(dataframe['close'], timeperiod=14)
        dataframe['rsi_angle'] = LINEARREG_ANGLE(dataframe['rsi'], timeperiod=5)


        # # first check if dataprovider is available
        # if self.dp:
        #     if self.dp.runmode in ('live', 'dry_run'):
        #         ob = self.dp.orderbook(metadata['pair'], 1)
        #         dataframe['best_bid'] = ob['bids'][0][0]
        #         dataframe['best_ask'] = ob['asks'][0][0]
        #
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                    (qtpylib.crossed_above(dataframe['macd'], dataframe['macdsignal'])) &
                    ((dataframe['macd_angle']) > -0.007579827857282747) &
                    (dataframe['tema'] < 0.124417394428206) &
                    (dataframe['sr_fastd_angle'] > -39) &
                    (dataframe['sf_fastk'] > 33) &
                    (dataframe['rsi_angle'] > 24) &
                    (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                    ((dataframe['macdhist']) < 0.000241872676925719) &
                    (dataframe['sr_fastd_angle'] > 71) &
                    (dataframe['sf_fastd_angle'] < 21) &
                    (dataframe['rsi_angle'] < 1) &
                    (dataframe['volume'] > 0)  # Make sure Volume is not 0
            ),
            'sell'] = 1
        return dataframe

