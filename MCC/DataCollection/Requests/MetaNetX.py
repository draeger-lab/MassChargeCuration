import requests
import logging
import time
import os
import pandas as pd
from difflib import SequenceMatcher
from ...util import progress_download

from .databaseInterface import DatabaseInterface


class MetaNetXInterface(DatabaseInterface):
    def __init__(self, data_path, no_local=False):
        init_start = time.perf_counter()
        self.data_path = data_path
        self.no_local = no_local
        self.load_metanetx_db()
        self.prop_dict = {}
        map_start = time.perf_counter()
        logging.info("Building MetaNetX property lookup dictionary...")
        if len(self.prop_df) > 0:
            self.prop_dict = dict(
                zip(
                    self.prop_df["#ID"],
                    zip(self.prop_df["formula"], self.prop_df["charge"]),
                )
            )
        else:
            logging.info(
                "MetaNetX property table is empty; lookup dictionary remains empty."
            )
        logging.info(
            f"[{time.perf_counter() - map_start:.3f} s] Built MetaNetX property lookup with {len(self.prop_dict)} entries."
        )
        logging.info(
            f"[{time.perf_counter() - init_start:.3f} s] MetaNetX interface initialization complete."
        )

    def _get_tsv_columns(self, filepath):
        """
        Reads the last comment line (starting with #) from a tsv file and returns the column names as a list.
        """
        header_line = None
        with open(filepath, "r") as f:
            for line in f:
                if line.startswith("#"):
                    header_line = line.strip()
                elif header_line is not None:
                    break
        if header_line is None:
            raise ValueError(f"No header line found in {filepath}")
        # Remove leading # and split by tab
        columns = [col.strip() for col in header_line.split("\t")]
        return columns

    def _load_cached_table(self, table_name, tsv_path):
        cache_path = f"{tsv_path}.pkl"
        tsv_mtime = os.path.getmtime(tsv_path)

        if os.path.exists(cache_path):
            cache_mtime = os.path.getmtime(cache_path)
            if cache_mtime >= tsv_mtime:
                cache_load_start = time.perf_counter()
                logging.info(
                    f"Loading MetaNetX {table_name} binary cache from {cache_path}"
                )
                try:
                    df = pd.read_pickle(cache_path)
                    logging.info(
                        f"[{time.perf_counter() - cache_load_start:.3f} s] Loaded MetaNetX {table_name} binary cache with {len(df)} rows."
                    )
                    return df
                except Exception as exc:
                    logging.warning(
                        f"Failed loading MetaNetX {table_name} binary cache ({exc}). Re-parsing TSV."
                    )

        tsv_load_start = time.perf_counter()
        logging.info(f"Parsing MetaNetX {table_name} TSV from {tsv_path}")
        tsv_columns = self._get_tsv_columns(tsv_path)
        df = pd.read_csv(tsv_path, sep="\t", comment="#", names=tsv_columns)
        logging.info(
            f"[{time.perf_counter() - tsv_load_start:.3f} s] Parsed MetaNetX {table_name} TSV with {len(df)} rows."
        )

        try:
            write_start = time.perf_counter()
            df.to_pickle(cache_path)
            logging.info(
                f"[{time.perf_counter() - write_start:.3f} s] Wrote MetaNetX {table_name} binary cache to {cache_path}"
            )
        except Exception as exc:
            logging.warning(
                f"Failed writing MetaNetX {table_name} binary cache ({exc}). Continuing with TSV-backed dataframe."
            )
        return df

    def load_metanetx_db(self):
        start = time.perf_counter()
        if self.no_local:
            logging.warning(
                "MetaNetX interface is currently only implemented to download the entire database."
            )
            self.xref_df = pd.DataFrame()
            self.depr_df = pd.DataFrame()
            self.prop_df = pd.DataFrame()
            return

        base_url = "https://www.metanetx.org/ftp/latest/{}"
        # chem_xref.tsv
        xref_path = f"{self.data_path}/chem_xref.tsv"
        try:
            self.xref_df = self._load_cached_table("xref", xref_path)
        except FileNotFoundError:
            logging.warning(
                "MetaNetX xref database not found. Downloading MetaNetX xref database, this might take a while..."
            )
            progress_download(base_url.format("chem_xref.tsv"), xref_path)
            self.xref_df = self._load_cached_table("xref", xref_path)
            logging.info("Downloaded and initialized MetaNetX xref cache.")

        # chem_depr.tsv
        depr_path = f"{self.data_path}/chem_depr.tsv"
        try:
            self.depr_df = self._load_cached_table("depr", depr_path)
        except FileNotFoundError:
            logging.warning(
                "MetaNetX depr database not found. Downloading MetaNetX depr database, this might take a while..."
            )
            progress_download(base_url.format("chem_depr.tsv"), depr_path)
            self.depr_df = self._load_cached_table("depr", depr_path)
            logging.info("Downloaded and initialized MetaNetX depr cache.")

        # chem_prop.tsv
        prop_path = f"{self.data_path}/chem_prop.tsv"
        try:
            self.prop_df = self._load_cached_table("prop", prop_path)
        except FileNotFoundError:
            logging.warning(
                "MetaNetX prop database not found. Downloading MetaNetX prop database, this might take a while..."
            )
            progress_download(base_url.format("chem_prop.tsv"), prop_path)
            self.prop_df = self._load_cached_table("prop", prop_path)
            logging.info("Downloaded and initialized MetaNetX prop cache.")
        logging.info(f"[{time.perf_counter() - start:.3f} s] MetaNetX database ready.")

    def get_assignments_by_id(self, meta_id):
        result = self.prop_dict.get(meta_id, None)
        if meta_id == "MNXM178":
            logging.info(f"Found for {meta_id} : {result}")
        return [result]

    def search_identifier(self, names, other_ids):
        id_mapping = {
            "metanetx.chemical": "mnx",  # somewhat redundant
            "bigg.metabolite": "bigg.metabolite",
            "seed.compound": "seed.compound",
            "sabiork.compound": "sabiork.compound",
            "biocyc": "metacyc.compound",
        }
        other_ids = [
            f"{id_mapping[db_id]}:{meta_id.replace('META:', '')}"
            for db_id, meta_ids in other_ids.items()
            for meta_id in meta_ids["ids"]
        ]
        return list(
            self.xref_df["ID"][
                self.xref_df["#source"].apply(lambda x: x in other_ids)
            ].unique()
        )

    def update_id(self, id):
        """
        Returns the old and new ids for the given id in MetaNetX.
        Only works with the downloaded depr file.

        Args:
            id: Id to update.

        Returns:
            Tuple of deprecated and new ids.
                => ([deprecated ids], [new ids])
        """
        current_ids = set([id])
        old_ids = set()
        remove = None
        while (remove is None) or len(remove) > 0:
            remove = set()
            new = set()
            for cur_id in current_ids:
                depr_rows = self.depr_df[self.depr_df["#deprecated_ID"] == (cur_id)]
                if len(depr_rows) > 0:
                    remove.add(cur_id)
                    new.update([metabolite_id for metabolite_id in depr_rows["ID"]])
            current_ids.update(new)
            current_ids -= remove
            old_ids.update(remove)
        return old_ids, current_ids

    def update_ids(self, ids, names):
        new_ids = set()
        names_and_ids = [*names, *ids]
        old_ids = set()
        for meta_id in ids:
            old, new = self.update_id(meta_id)
            # filter for most similar name
            filtered_new = []
            for mid in new:
                found_names = self.prop_df["name"][self.prop_df["#ID"] == mid]
                if len(found_names) == 0:
                    continue
                max_sim = max(
                    found_names.apply(
                        lambda x: max([similar(x, name) for name in names_and_ids])
                    )
                )
                filtered_new.append((max_sim, mid))
            if len(filtered_new) == 0:
                continue
            max_similarity = max([scored[0] for scored in filtered_new])
            if (max_similarity > 0.8) and (len(new) > 1):
                filtered_meta_ids = [
                    scored[1]
                    for scored in filtered_new
                    if scored[0] > max_similarity * 0.9
                ]
                removed_meta_ids = [
                    scored[1]
                    for scored in filtered_new
                    if scored[0] <= max_similarity * 0.9
                ]
            else:
                filtered_meta_ids = []
                removed_meta_ids = [scored[1] for scored in filtered_new]
                # logging.warning(f"Max metanetX similarity for {metabolite.id} was less then .8 with {filtered_meta_ids} chosen.")
            new_ids.update(filtered_meta_ids)
            new_ids.difference_update(old)
            new_ids.difference_update(removed_meta_ids)
            old_ids.update(removed_meta_ids)
            old_ids.update(old)
        return old_ids, new_ids

    def get_other_references(self, id, relevant_dbs):
        id_mapping = {
            "mnx": "metanetx.chemical",  # somewhat redundant
            "bigg.metabolite": "bigg.metabolite",
            "seed.compound": "seed.compound",
            "sabiork.compound": "sabiork.compound",
            "metacyc.compound": "biocyc",
        }
        references = {}
        out_refs = self.xref_df["#source"][self.xref_df["ID"] == id]

        def split_into_identifiers(s):
            colon_index = s.find(":")
            if colon_index > -1:
                db_identifier = s[:colon_index]
                meta_id = s[colon_index + 1 :]
                if db_identifier in id_mapping:
                    db_ref = references.get(db_identifier, set())
                    db_ref.add(meta_id.replace("META:", ""))
                    references[id_mapping[db_identifier]] = db_ref

        out_refs.apply(split_into_identifiers)
        return references


def similar(a, b):
    """
    Determines similarity between two strings. If a starts with L, than b must also start with L.
    Otherwise we return 0.

    Args:
        a (str): first string to compare.
        b (str): Second string to compare.

    Returns:
        String similarity.
    """
    if a.startswith("L ") or a.startswith("L-"):
        if not (b.startswith("L ") or b.startswith("L-")):
            return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
