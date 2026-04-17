import numpy as np
import os
import logging
import time
from tqdm import tqdm
import dill

from ..ModelInterface.ModelInterface import ModelInterface
from ..core import Formula, Metabolite

from .Requests.BiGG import BiGGInterface
from .Requests.BioCyc import BioCycInterface
from .Requests.MetaNetX import MetaNetXInterface
from .Requests.ModelSEED import ModelSEEDInterface


default_interfaces = {
    "metanetx.chemical": MetaNetXInterface,
    "bigg.metabolite": BiGGInterface,
    "seed.compound": ModelSEEDInterface,
    "biocyc": BioCycInterface,
}


def default_data_path():
    """
    Returns a stable cache directory for downloaded database artifacts.
    """
    xdg_cache = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache:
        cache_root = xdg_cache
    else:
        cache_root = os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(cache_root, "MassChargeCuration")


class DataCollector:
    """
    Class intended to be used by the ModelBalancer to gather the information for the metabolites from different databases.
    Uses further specified interfaces to different databases to gather the data, cleans the gathered formulae and provides a function to
    gather the ids for different databases for the metabolites based on the present information.

    The class can be used with online and offline resources, however, full functionality is only given if both can be used.

    Args:
        model (cobrapy.Model): Model for which the DataCollector will gather the information and takes information to gather ids.
        data_path (string): Optional; Path where offline data is searched for/downloaded to.
        update_ids (bool): Optional; Whether or not to gather/update the database identifiers for the used databases.
        gather_information (bool): Optional; If False, will not actually gather any information. Useful if you like
            to register other interfaces first, or only want to update ids.
        used_annotations ([str]): Optional; Annotations to use, defaults to all. If you distrust a certain database or only want to use a specific one
            you can specify which databases to use here.
        no_local (bool): Optional; Whether or not to use local data/ download database files.
        biocyc_path (str): Optional; Path to biocyc database files.
        cache_ids (str): Optional; Name of cache file for the metabolite ids in the data_path. If given, will load the ids from the cache file instead of updating them.
    """

    def __init__(
        self,
        model=None,
        data_path=None,
        update_ids=False,
        gather_information=True,
        used_annotations=None,
        no_local=False,
        biocyc_path=None,
        cache_ids=None,
    ):
        is_warm_up_mode = (
            (model is None) and (not update_ids) and (not gather_information)
        )
        if model is None:
            if is_warm_up_mode:
                logging.info(
                    "Initializing DataCollector in warm-up mode without a model."
                )
            else:
                logging.warning(
                    "No model was passed to DataCollector. This is most likely not intended."
                )
        else:
            self.model_interface = ModelInterface(model)
        self.no_local = no_local
        self.interfaces = {}
        self.used_annotations = (
            list(default_interfaces.keys())
            if used_annotations is None
            else used_annotations
        )
        self.data_path = default_data_path() if data_path is None else data_path
        self.strict_linkback = True
        cache_dir_exists = os.path.isdir(self.data_path)
        os.makedirs(self.data_path, exist_ok=True)
        if cache_dir_exists:
            logging.info(f"Using existing cache directory: {self.data_path}")
        else:
            logging.info(f"Created cache directory: {self.data_path}")
        logging.info(f"Configured interfaces: {self.used_annotations}")
        logging.info(f"Local cache usage enabled: {not self.no_local}")
        self._load_default_interfaces(self.data_path, biocyc_path)
        self.assignments = {}
        self.allow_undefined_charge = True
        if update_ids:
            if cache_ids:
                raise NotImplementedError(
                    "Caching of ids is currently not implemented."
                )
                cache_path = os.path.join(self.data_path, cache_ids)
                if os.path.exists(cache_path):
                    with open(cache_path, "rb") as f:
                        dill.load(f)

                else:
                    self.get_all_ids()
                    with open(cache_path, "wb") as f:
                        dill.dump(self.model_interface.metabolites, f)
            else:
                self.get_all_ids()
        if gather_information:
            self.gather_info()

    @classmethod
    def warm_up(
        cls, data_path=None, used_annotations=None, no_local=False, biocyc_path=None
    ):
        """
        Preloads and caches the configured external database artifacts without requiring a model.

        Args:
            data_path (str): Optional cache directory for downloaded database artifacts.
            used_annotations ([str]): Optional subset of database interfaces to preload.
            no_local (bool): If True, skips local artifact download/consolidation.
            biocyc_path (str): Optional BioCyc base path for consolidating BioCyc into the local cache.

        Returns:
            DataCollector configured with the requested interfaces and warmed caches.
        """
        cls._configure_warm_up_logging()
        if data_path is None:
            data_path = default_data_path()
        warm_up_start = time.perf_counter()
        logging.info(f"Starting cache warm-up in {data_path}")
        logging.info(
            f"Requested interfaces: {used_annotations if not (used_annotations is None) else 'all default interfaces'}"
        )
        logging.info(f"Using local cache artifacts: {not no_local}")
        if biocyc_path is None:
            logging.info(
                "BioCyc base path: not provided (using cached BioCyc if available)."
            )
        else:
            logging.info(f"BioCyc base path: {biocyc_path}")
        collector = cls(
            model=None,
            data_path=data_path,
            update_ids=False,
            gather_information=False,
            used_annotations=used_annotations,
            no_local=no_local,
            biocyc_path=biocyc_path,
            cache_ids=None,
        )
        logging.info(
            f"[{time.perf_counter() - warm_up_start:.3f} s] Finished warming external database caches."
        )
        return collector

    @classmethod
    def _configure_warm_up_logging(cls):
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            logging.basicConfig(
                format="%(levelname)s: %(filename)s %(lineno)d, %(funcName)s: %(message)s",
                level=logging.INFO,
            )
            logging.info(
                "No logging handlers detected. Enabled INFO logging for warm-up progress."
            )

    def _load_default_interfaces(self, data_path, biocyc_path=None):
        """
        Function to load all the default interfaces, specified in default_interfaces at the top of the file.
        Currently compromised of BiGG, MetaNetX, BioCyc and ModelSEED.

        Args:
            data_path: Path for the offline database files.
            biocyc_path: Optional; Path for the BioCyc offline database file.
        """
        unknown_annotations = sorted(
            set(self.used_annotations).difference(default_interfaces.keys())
        )
        if len(unknown_annotations) > 0:
            logging.warning(
                f"Unknown annotations requested and ignored: {unknown_annotations}"
            )

        selected_identifiers = [
            identifier
            for identifier in default_interfaces.keys()
            if self.used_annotations is None or identifier in self.used_annotations
        ]
        logging.info(
            f"Loading {len(selected_identifiers)} data interfaces: {selected_identifiers}"
        )

        for identifier in selected_identifiers:
            constructor = default_interfaces[identifier]
            load_start = time.perf_counter()
            logging.info(f"Loading data interface '{identifier}'...")
            try:
                if identifier == "biocyc":
                    interface = constructor(
                        data_path, no_local=self.no_local, biocyc_base_path=biocyc_path
                    )
                else:
                    interface = constructor(data_path, no_local=self.no_local)
            except Exception:
                logging.exception(f"Failed loading data interface '{identifier}'.")
                raise
            self.register_interface(identifier, interface)
            logging.info(
                f"[{time.perf_counter() - load_start:.3f} s] Loaded data interface '{identifier}'."
            )

    def register_interface(self, identifier, interface):
        """
        Function to register a database interface.

        Args:
            identifier (str): Name of the identifiers.org identifier. Should be the same as in metabolite.annotation.
            interface (MCC.DatabaseInterface): Database interface. Should inherit from MCC.DatabaseInterface.
        """
        self.interfaces[identifier] = interface

    def get_formulae(self, metabolite: Metabolite):
        """
        Function to gather all available formulae/charges with the given interfaces.

        Args:
            metabolite (core.Metabolite): Metabolite for which to gather the formulae/charges.

        Returns:
            Dictionary mapping all found formulae/charges to the containing databases.
                => {(formula, charge): set(database_identifiers)}

        """
        assignments = {}
        annotations = metabolite.cv_terms
        for db_id, interface in self.interfaces.items():
            ids = annotations.get(db_id, [])
            for identifier in ids:
                try:
                    if not (
                        (cur_assignments := interface.get_assignments_by_id(identifier))
                        is None
                    ):
                        logging.debug(f"{db_id}, {identifier}")
                        for assignment in cur_assignments:
                            if assignment is None:
                                continue
                            if (type(assignment[0]) == float) or (
                                assignment[0] is None
                            ):
                                continue
                            if (
                                (type(assignment[1]) == float)
                                and np.isnan(assignment[1])
                                or (assignment[1] is None)
                            ):
                                if self.allow_undefined_charge:
                                    assignment = (Formula(assignment[0]), None)
                                else:
                                    continue
                            assignment = (
                                Formula(assignment[0]),
                                int(assignment[1])
                                if not assignment[1] is None
                                else None,
                            )
                            cur_db = assignments.get(assignment, set())
                            cur_db.add((db_id, identifier))
                            assignments[assignment] = cur_db
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logging.exception(
                        f"Error getting formula for {identifier} in {db_id}:"
                    )

        return assignments

    def gather_info(self):
        """
        Gathers formulae and charges for all metabolites in self.model.
        """
        for i, metabolite in tqdm(
            enumerate(self.model_interface.metabolites.values()),
            total=len(self.model_interface.metabolites),
            desc="Gathering information for metabolites",
        ):
            logging.debug(
                f"{i + 1}/{len(self.model_interface.metabolites)}: Getting information for {metabolite.id}"
            )
            self.assignments[metabolite.id] = self.get_formulae(metabolite)

    def get_assignments(
        self, metabolite: Metabolite, clean=True, partial=True, database_seperated=False
    ):
        """
        Function to return all assignments for the given metabolite that were found using all registered interfaces.

        Args:
            metabolite (cobrapy.Metabolite): Metabolite for which to gather information.
            clean (bool): Whether or not to also return formulae which were not cleaned (False currently not implemented).
            partial (bool): Whether or not to return formulae containing wildcard symbols (False currently not implemented).
            database_seperated (bool): Whether or not to return formulae mapping to the databases that contain them.

        Returns:
            If database_seperated = False: Set of formula/charge combinations that could be found for this metabolite.
            Otherwise: Dictionary mapping (formula, charge) to set of database identifiers where it could be found.

        """
        if len(self.assignments) == 0:
            logging.warn(
                "Tried to get assignments with no gathered information. Try calling gather_info before."
            )
            return None
        assignments = self.assignments.get(metabolite.id, {})
        if metabolite.notes.get("type", "metabolite") != "class":
            filtered_assignments = {
                assignment: databases
                for assignment, databases in assignments.items()
                if not ("R" in assignment[0])
            }
            if len(filtered_assignments) > 0:
                assignments = filtered_assignments
        if (clean == False) or (partial == False):
            raise NotImplementedError

        if database_seperated:
            return assignments
        else:
            return set(assignments.keys())

    def get_all_ids(self):
        """
        Updates/gathers all ids for all metabolites in the currently registered database interfaces.
        """
        now = time.process_time()
        total_new_ids = 0
        for i, metabolite in tqdm(
            enumerate(self.model_interface.metabolites.values()),
            total=len(self.model_interface.metabolites),
            desc="Gathering ids for metabolites",
        ):
            ids = self.get_ids(metabolite)
            total_new_ids += ids[2]
            logging.debug(f"Ids were {ids}")
            annotations = metabolite.cv_terms
            for db in self.used_annotations:
                if db == "biocyc":
                    annotations[db] = [f"META:{entry}" for entry in ids[0][db]["ids"]]
                else:
                    annotations[db] = list(ids[0][db]["ids"])
            logging.debug(
                f"Updated metabolite {metabolite.id} annotations to {annotations}"
            )
        logging.info(
            f"[{time.process_time() - now:.3f} s] Gathered Ids. {total_new_ids} new ids found."
        )

    def get_ids(self, metabolite: Metabolite):
        """
        Updates/gathers all ids for the given metabolite in the currently registered database interfaces.

        Args:
            metaoblite (cobrapy.Metabolite): Metabolite for which to gather the ids.

        Returns:
            Dictionary mapping database identifiers to outdated and current ids.
                => {db_identifer : {"old_ids" : [outdated ids], "ids" : set(current ids)}}
        """

        names = (
            [metabolite.name]
            if metabolite.name
            else ([metabolite.id[2:], metabolite.id] if metabolite.id else [])
        )
        DB_ids = {
            db_identifier: {"old_ids": [], "ids": set()}
            for db_identifier in self.used_annotations
        }
        missing_links = set(self.used_annotations)
        check_list = set()
        # taking ids from annotations
        annotations = metabolite.cv_terms
        for db_identifier in annotations:
            if db_identifier in self.used_annotations:
                if type(annotations[db_identifier]) is list:
                    DB_ids[db_identifier]["ids"].update(
                        [
                            meta_id.replace("META:", "")
                            for meta_id in annotations[db_identifier]
                        ]
                    )
                else:
                    DB_ids[db_identifier]["ids"].add(
                        annotations[db_identifier].replace("META:", "")
                    )
                check_list.update(
                    [
                        (db_identifier, meta_id.replace("META:", ""))
                        for meta_id in DB_ids[db_identifier]["ids"]
                    ]
                )
                missing_links.remove(db_identifier)

        # fetching missing ids from other information
        new_ids_found = 0
        for db_identifier in missing_links:
            try:
                if (
                    not (
                        found := self.interfaces[db_identifier].search_identifier(
                            names, DB_ids
                        )
                    )
                    is None
                ) and (len(found) > 0):
                    DB_ids[db_identifier]["ids"].update(found)
                    new_ids_found += len(found)
                    logging.debug(
                        f"Found new ids {found} in {db_identifier} via id & name based search for {metabolite.id}"
                    )
                    check_list.update(
                        [
                            (db_identifier, meta_id.replace("META:", ""))
                            for meta_id in DB_ids[db_identifier]["ids"]
                        ]
                    )
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.exception(f"Error searching for identifier in {db_identifier}:")

        # update identifiers
        flattened_ids = [
            meta_id.replace("META:", "")
            for meta_ids in DB_ids.values()
            for meta_id in meta_ids["ids"]
        ]
        for db_identifier in self.interfaces:
            try:
                old, new = self.interfaces[db_identifier].update_ids(
                    flattened_ids, names
                )
                check_list.difference_update(
                    [(db_identifier, meta_id) for meta_id in old]
                )
                DB_ids[db_identifier]["ids"].difference_update(old)
                check_list.update([(db_identifier, meta_id) for meta_id in new])
                DB_ids[db_identifier]["ids"].update(new)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.exception(f"Error updating identifier in {db_identifier}:")

        # iteratively trying to gather more ids and pruning potential metaNetX ids
        while len(check_list) > 0:
            next_id = check_list.pop()
            try:
                result = self.interfaces[next_id[0]].get_other_references(
                    next_id[1], self.used_annotations
                )
                if result is None:
                    continue
                for database_id, meta_ids in result.items():
                    if (meta_ids is None) or (database_id not in self.used_annotations):
                        continue
                    flattened_ids = []
                    for meta_id in meta_ids:
                        if type(meta_id) == list:
                            flattened_ids.extend(meta_id)
                        else:
                            flattened_ids.append(meta_id)
                    for meta_id in flattened_ids:
                        meta_id = meta_id.replace("META:", "")
                        if meta_id not in DB_ids[database_id]["ids"]:
                            if meta_id in DB_ids[database_id]["old_ids"]:
                                _, new_ids = self.interfaces[database_id].update_ids(
                                    meta_id
                                )
                            else:
                                new_ids = [meta_id]
                            for meta_id in new_ids:
                                back_references = self.interfaces[
                                    database_id
                                ].get_other_references(meta_id, self.used_annotations)
                                back_ref = back_references.get(next_id[0], [])
                                strict_condition = (
                                    self.strict_linkback or len(back_references) != 0
                                )
                                if (not strict_condition) or (
                                    (not back_ref is None) and (next_id[1] in back_ref)
                                ):
                                    DB_ids[database_id]["ids"].add(meta_id)
                                    check_list.add((database_id, meta_id))
                                    logging.info(
                                        f"Found new id {meta_id} in {database_id} from {next_id} for {metabolite.id}"
                                    )
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logging.exception(f"Error getting other identifiers: {next_id}")
        return DB_ids, names, new_ids_found
