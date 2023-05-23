"""THIS IS AUTOMATICALLY GENERATED CODE, DO NOT MANUALLY MODIFY!"""
from cdp.cdp_comm import *


# object: Metric
class Metric(TypingT):
    """
        Run-time execution metric.
    """
    def __init__(self):
        # Metric name.
        self.name: str = str
        # Metric value.
        self.value: int = int


# event: metrics
class metrics(EventT):
    """
        Current values of the metrics.
    """
    event="Performance.metrics"
    def __init__(self):
        # Current values of the metrics.
        self.metrics: List[Metric] = [Metric]
        # Timestamp title.
        self.title: str = str


# ================================================================================
# Performance Domain.
# ================================================================================
class Performance(DomainT):
    """
        Performance
    """
    def __init__(self, drv):
        self.drv = drv


    # func: disable
    def disable(self):
        """
            Disable collecting and reporting metrics.
        """
        return self.drv.call(None,'Performance.disable')


    # func: enable
    def enable(self,timeDomain:str=None):
        """
            Enable collecting and reporting metrics.
        Params:
            timeDomainEnums = ['timeTicks', 'threadTicks']
            1. timeDomain: str (OPTIONAL)
                Time domain to use for collecting and reporting duration metrics.
        """
        return self.drv.call(None,'Performance.enable',timeDomain=timeDomain)


    # func: setTimeDomain
    def setTimeDomain(self,timeDomain:str):
        """
            Sets time domain to use for collecting and reporting duration metrics.
            Note that this must be called before enabling metrics collection. Calling
            this method while metrics collection is enabled returns an error.
        Params:
            timeDomainEnums = ['timeTicks', 'threadTicks']
            1. timeDomain: str
                Time domain
        """
        return self.drv.call(None,'Performance.setTimeDomain',timeDomain=timeDomain)


    # return: getMetricsReturn
    class getMetricsReturn(ReturnT):
        def __init__(self):
            # Current values for run-time metrics.
            self.metrics: List[Metric] = [Metric]


    # func: getMetrics
    def getMetrics(self) -> getMetricsReturn:
        """
            Retrieve current values of run-time metrics.
        Return: getMetricsReturn
        """
        return self.drv.call(Performance.getMetricsReturn,'Performance.getMetrics')



