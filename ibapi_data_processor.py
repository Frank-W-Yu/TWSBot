import imp
from ibapi.common import BarData
from typing import Dict, Any


class IBDataProcessor:
    @classmethod
    def bar_to_dict(cls, bar: BarData) -> Dict[str, Any]:
        return {
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume,
            'bar_count': bar.barCount,
            'average': bar.average,
        }
