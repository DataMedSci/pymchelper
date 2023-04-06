import logging
import json

from pymchelper.axis import MeshAxis
from pymchelper.estimator import Estimator
from pymchelper.page import Page


logger = logging.getLogger(__name__)

class JsonWriter:
    """
    Supports writing JSON format.
    """

    def __init__(self, filename, options):
        self.filename = filename
        if not self.filename.endswith(".json"):
            self.filename += ".json"

    def write(self, estimator: Estimator):
        if len(estimator.pages) == 0:
            print("No pages in the output file, conversion to JSON skipped.")
            return False

        
        est_dict = {
            "metadata": {},
            "pages": []
        }

        # read metadata from estimator object
        for name, value in estimator.__dict__.items():
            # skip non-metadata fields
            if name not in {"data", "data_raw", "error", "error_raw", "counter", "pages", "x", "y", "z"}:
                # remove \" to properly generate JSON
                est_dict["metadata"][name] = str(value).replace("\"", "")

        for page in estimator.pages:
            # page_dict contains:
            # "dimensions" indicating it is 1 dim page
            # "data" which has unit, name and list of data values
            page: Page
            page_dict = {
                "metadata": {},
                "dimensions": page.dimension,
                "data": {
                    "unit": str(page.unit),
                    "name": str(page.name),
                }
            }

            # read metadata from page object
            for name, value in page.__dict__.items():
                # skip non-metadata fields and fields already read from estimator object
                exclude = {"data_raw", "error_raw", "estimator", "diff_axis1", "diff_axis2"}
                exclude |= set(estimator.__dict__.keys())
                if name not in exclude:
                    # remove \" to properly generate JSON
                    page_dict["metadata"][name] = str(value).replace("\"", "")

            if page.dimension == 0:
                page_dict["data"]["values"] = [page.data_raw.tolist()]
            else:
                page_dict["data"]["values"] = page.data_raw.tolist()
            # currently output is returned only when dimension == 1 due to
            # problems in efficient testing of other dimensions

            ################ Old code start ################
            # if page.dimension in {1, 2}:
            #     axis: MeshAxis = page.plot_axis(0)
            #     page_dict["first_axis"] = {
            #         "unit": str(axis.unit),
            #         "name": str(axis.name),
            #         "values": axis.data.tolist(),
            #     }
            # if page.dimension == 2:
            #     axis: MeshAxis = page.plot_axis(1)
            #     page_dict["second_axis"] = {
            #         "unit": str(axis.unit),
            #         "name": str(axis.name),
            #         "values": axis.data.tolist(),
            #     }
            # if page.dimension > 2:
            #     # Add info about the location of the file containging to many dimensions
            #     raise ValueError(f"Invalid number of pages {page.dimension}")
            ################  Old code end  ################
            for i in range(page.dimension):
                axis: MeshAxis = page.plot_axis(i)
                page_dict[f"{i+1}_axis"] = {
                    "unit": str(axis.unit),
                    "name": str(axis.name),
                    "values": axis.data.tolist(),
                }

            est_dict["pages"].append(page_dict)

        with open(self.filename, "w") as json_file:
            json.dump(est_dict, json_file)

        return 0
