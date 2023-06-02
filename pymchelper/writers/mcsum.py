import logging
import time
import urllib.parse

logger = logging.getLogger(__name__)


class MCSumWriter:
    def __init__(self, filename, options):
        logger.debug("Initialising Inspector writer")
        self.options = options

    @staticmethod
    def write(estimator):
        """Print all keys and values from estimator structure

        they include also a metadata read from binary output file
        """
        s = estimator.total_run_time
        if s < 60:
            ts = time.strftime('%S seconds', time.gmtime(s))
        elif s < 3600:
            ts = time.strftime('%M minutes', time.gmtime(s))
        else:
            ts = time.strftime('%H hours %M minutes', time.gmtime(s))

        print('Item name |  Description | References')
        print('|---|---|---|')
        print(f'| Code Version | {estimator.mc_code_version} | |')
        print('| Validation | |')
        print(f'| Timing | {estimator.file_counter} jobs, {ts} total runtime |')
        print('| Geometry | |')
        print('| Source | |')
        print('| Physics | |')
        print('| Scoring | |')
        print(f'|\\# histories | {estimator.total_number_of_primaries} | |')

        url = urllib.parse.quote("https://doi.org/10.1002/mp.12702", safe="")
        url = "https://doi.org/10.1002/mp.12702"
        print('Table caption: Summary of Monte Carlo simulations parameters in AAPM TG268 format.')
        print(f'[See Sechopoulos et al. (2018), {url}.]')
        return 0
