import os
import pandas as pd
from collections import defaultdict
import unidecode

WISH_ENSEIGNANT_COLUMN = "Enseignant"
WISH_SEMESTRE_COLUMN = "Semestre"
WISH_SESSION_COLUMN = "Session"
WISH_JOUR_COLUMN = "Jour"
WISH_SEANCES_COLUMN = "Séances"
WISH_COLUMNS = [
    WISH_ENSEIGNANT_COLUMN,
    WISH_SEMESTRE_COLUMN,
    WISH_SESSION_COLUMN,
    WISH_JOUR_COLUMN,
    WISH_SEANCES_COLUMN,
]

def preprocess_exam_info(salle_date_excel_path: str):
    """
    Preprocesses exam schedule data from an Excel file.

    Parameters:
    -----------
    salle_date_excel_path : str
        Path to the Excel file containing exam schedule info.

    Returns:
    --------
    tuple[dict, dict, pd.DataFrame]
        - profs_by_session: dict mapping "date+time" -> set of professor IDs
        - rooms_by_session: dict mapping "date+time" -> number of rooms used
        - cleaned DataFrame (df_info)
    """

    # ✅ Load the Excel file into a DataFrame
    df_info = pd.read_excel(salle_date_excel_path)

    # ✅ Clean time columns — remove fake date part, keep only HH:MM
    df_info["h_debut"] = (
        df_info["h_debut"]
        .astype(str)
        .str.extract(r"(\d{2}:\d{2})")[0]
        .fillna("00:00")
    )
    df_info["h_fin"] = (
        df_info["h_fin"]
        .astype(str)
        .str.extract(r"(\d{2}:\d{2})")[0]
        .fillna("00:00")
    )

    # ✅ Clean date column — keep only DD/MM
    df_info["dateExam"] = (
        df_info["dateExam"]
        .astype(str)
        .str.extract(r"(\d{2}/\d{2})")[0]
        .fillna("00/00")
    )

    # ✅ Prepare containers
    profs_by_session = defaultdict(set)
    rooms_by_session = defaultdict(int)

    # ✅ Process each row
    for _, row in df_info.iterrows():
        # Unique session key (date + start time)
        key = f"{row['dateExam']} {row['h_debut']}"
        prof_id = str(row["enseignant"]).strip()

        # Add professor ID if valid
        if prof_id not in ("0", "", "nan") and prof_id.lower() != "nan":
            profs_by_session[key].add(prof_id)

        # Count room usage
        rooms_by_session[key] += 1

    # ✅ Debug printouts (optional — can disable in production)
    print("\n[Professors by session]")
    for k, v in profs_by_session.items():
        print(f"{k:<15} → {len(v)} professors")

    print("\n[Rooms by session]")
    for k, v in rooms_by_session.items():
        print(f"{k:<15} → {v} rooms")

    # ✅ Return results
    return profs_by_session, rooms_by_session


def preprocess_professors(professors_excel_path: str, wishes_excel_path: str) -> pd.DataFrame:
    """
    Combines professor info and their surveillance wishes into a single DataFrame.
    Excludes professors not participating in surveillance.
    """

    # --- 1️⃣ Load both Excel files ---
    df_profs = pd.read_excel(professors_excel_path)
    if wishes_excel_path is None or not os.path.exists(wishes_excel_path):
        df_wishes = pd.DataFrame(columns=WISH_COLUMNS)
    else:
        df_wishes = pd.read_excel(wishes_excel_path)

    df_submission = pd.DataFrame(columns=[WISH_ENSEIGNANT_COLUMN, "wish_submission_index"])
    if not df_wishes.empty:
        if WISH_ENSEIGNANT_COLUMN not in df_wishes.columns and "enseignant" in df_wishes.columns:
            df_wishes = df_wishes.rename(columns={"enseignant": WISH_ENSEIGNANT_COLUMN})

        df_submission = (
            df_wishes.groupby(WISH_ENSEIGNANT_COLUMN)
            .apply(lambda values: values.index.min())
            .reset_index()
        )
        df_submission.columns = [WISH_ENSEIGNANT_COLUMN, "wish_submission_index"]

    # --- 2️⃣ Clean and normalize base professor data ---
    df_profs = df_profs.copy()
    df_profs["nom_complet"] = df_profs["nom_ens"].str.strip() + " " + df_profs["prenom_ens"].str.strip()
    df_profs["id"] = pd.to_numeric(df_profs["code_smartex_ens"], errors="coerce").astype("Int64")
    df_profs["grade"] = df_profs["grade_code_ens"].astype(str).str.strip()
    df_profs["participe"] = df_profs["participe_surveillance"].astype(str).str.lower().str.strip()

    # --- 3️⃣ Drop non-participating professors early ---
    df_profs = df_profs[df_profs["participe"].str.lower() == "true"].reset_index(drop=True)

    # --- 4️⃣ Clean and normalize wishes data ---
    day_map = {
        "lundi": 0,
        "mardi": 1,
        "mercredi": 2,
        "jeudi": 3,
        "vendredi": 4,
        "samedi": 5,
    }

    if not df_wishes.empty:
        if WISH_SEANCES_COLUMN not in df_wishes.columns and "seance" in df_wishes.columns:
            df_wishes = df_wishes.rename(columns={"seance": WISH_SEANCES_COLUMN})
        if WISH_JOUR_COLUMN not in df_wishes.columns and "jour" in df_wishes.columns:
            df_wishes = df_wishes.rename(columns={"jour": WISH_JOUR_COLUMN})

        df_wishes = df_wishes.copy()
        df_wishes[WISH_ENSEIGNANT_COLUMN] = df_wishes[WISH_ENSEIGNANT_COLUMN].astype(str).str.strip()
        df_wishes[WISH_JOUR_COLUMN] = df_wishes[WISH_JOUR_COLUMN].astype(str).str.strip().str.lower().map(lambda value: day_map.get(value, value))
        df_wishes[WISH_SEANCES_COLUMN] = df_wishes[WISH_SEANCES_COLUMN].astype(str).str.split(",")
        df_wishes = df_wishes.explode(WISH_SEANCES_COLUMN)
        df_wishes[WISH_SEANCES_COLUMN] = df_wishes[WISH_SEANCES_COLUMN].astype(str).str.strip().str.lower()
        df_wishes = df_wishes[(df_wishes[WISH_SEANCES_COLUMN] != "") & (df_wishes[WISH_SEANCES_COLUMN].str.lower() != "nan")]
        df_wishes[WISH_JOUR_COLUMN] = pd.to_numeric(df_wishes[WISH_JOUR_COLUMN], errors="coerce")
        df_wishes = df_wishes[df_wishes[WISH_JOUR_COLUMN].notna()]
        df_wishes[WISH_JOUR_COLUMN] = df_wishes[WISH_JOUR_COLUMN].astype(int)

        df_wishes_agg = (
            df_wishes.sort_values([WISH_ENSEIGNANT_COLUMN, WISH_JOUR_COLUMN])
            .groupby(WISH_ENSEIGNANT_COLUMN)
            .agg({
                WISH_JOUR_COLUMN: lambda values: ",".join(map(str, values)),
                WISH_SEANCES_COLUMN: lambda values: ",".join(values),
            })
            .reset_index()
        )
    else:
        df_wishes_agg = pd.DataFrame(columns=WISH_COLUMNS)

    # --- 5️⃣ Merge wishes with professor info ---
    df_profs["abrv_ens"] = df_profs["abrv_ens"].astype(str).str.strip()
    df_profs = pd.merge(
        df_profs,
        df_submission,
        left_on="abrv_ens",
        right_on=WISH_ENSEIGNANT_COLUMN,
        how="left",
        validate="many_to_one"
    )
    max_submission_index = df_submission["wish_submission_index"].max() if not df_submission.empty else -1
    default_submission_index = int(max_submission_index) + 1
    df_profs["wish_submission_index"] = pd.to_numeric(df_profs["wish_submission_index"], errors="coerce")
    df_profs["wish_submission_index"] = df_profs["wish_submission_index"].fillna(default_submission_index).astype(int)
    if WISH_ENSEIGNANT_COLUMN in df_profs.columns:
        df_profs = df_profs.drop(columns=[WISH_ENSEIGNANT_COLUMN])

    df_final = pd.merge(
        df_profs,
        df_wishes_agg,
        left_on="abrv_ens",
        right_on=WISH_ENSEIGNANT_COLUMN,
        how="left",
        validate="many_to_one"
    )

    # --- 7️⃣ Fill NaNs for those with no wishes ---
    df_final[WISH_JOUR_COLUMN] = df_final[WISH_JOUR_COLUMN].fillna("")
    df_final[WISH_SEANCES_COLUMN] = df_final[WISH_SEANCES_COLUMN].fillna("")

    # --- 8️⃣ Keep only useful columns ---
    df_final = df_final[["id", "nom_complet", "grade", "wish_submission_index", WISH_JOUR_COLUMN, WISH_SEANCES_COLUMN]]
    df_final = df_final.rename(columns={WISH_JOUR_COLUMN: "jour", WISH_SEANCES_COLUMN: "seance"})

    return df_final
