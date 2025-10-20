import pandas as pd
from collections import defaultdict
import unidecode

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
        if prof_id and prof_id.lower() != "nan":
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
    df_wishes = pd.read_excel(wishes_excel_path)

    # --- 2️⃣ Clean and normalize base professor data ---
    df_profs = df_profs.copy()
    df_profs["nom_complet"] = df_profs["nom_ens"].str.strip() + " " + df_profs["prenom_ens"].str.strip()
    df_profs["id"] = df_profs["code_smartex_ens"].astype(pd.Int64Dtype())
    df_profs["grade"] = df_profs["grade_code_ens"].astype(str).str.strip()
    df_profs["participe"] = df_profs["participe_surveillance"].astype(str).str.lower().str.strip()

    # --- 3️⃣ Drop non-participating professors early ---
    df_profs = df_profs[df_profs["participe"].str.lower() == "true"].reset_index(drop=True)

    # --- 4️⃣ Clean and normalize wishes data ---
    df_wishes["nom_complet"] = df_wishes["enseignant_uuid.nom_ens"].str.strip() + " " + df_wishes["enseignant_uuid.prenom_ens"].str.strip()
    df_wishes["jour"] = df_wishes["jour"].astype(int)
    df_wishes["seance"] = df_wishes["seance"].str.lower().str.strip()  # s1, s2, etc.

    # --- 5️⃣ Aggregate wishes per professor ---
    df_wishes_agg = (
    df_wishes.sort_values(["nom_complet", "jour"])
             .groupby("nom_complet")
             .agg({
                 "jour": lambda x: ",".join(map(str, x)),
                 "seance": lambda x: ",".join(x)
             })
             .reset_index()
    )

    # --- 6️⃣ Merge wishes with professor info ---
    
    # Normalize professor names
    df_profs["nom_complet_norm"] = df_profs["nom_complet"].str.lower().str.strip().apply(unidecode.unidecode)
    df_wishes_agg["nom_complet_norm"] = df_wishes_agg["nom_complet"].str.lower().str.strip().apply(unidecode.unidecode)
    
    # --- DEBUG PRINTS ---
    print("\n[Professors DataFrame]")
    print(df_profs[["nom_complet", "id"]])
    print(f"Total professors: {len(df_profs)}\n")

    print("[Wishes Aggregated DataFrame]")
    print(df_wishes_agg)
    print(f"Total professors with wishes: {len(df_wishes_agg)}\n")

    # Check which professors have a matching wish
    matches = df_profs["nom_complet_norm"].isin(df_wishes_agg["nom_complet_norm"])
    print(f"Professors with matching wishes: {matches.sum()} / {len(df_profs)}")
    print("Matching professors:")
    print(df_profs[matches][["nom_complet", "id"]])

    df_final = pd.merge(df_profs, df_wishes_agg, left_on="nom_complet_norm", right_on="nom_complet_norm", how="left")
    print("Columns after merge:", df_final.columns.tolist())

    # --- 7️⃣ Fill NaNs for those with no wishes ---
    df_final[["jour", "seance"]] = df_final[["jour", "seance"]].fillna("")

    # --- 8️⃣ Keep only useful columns ---
    df_final = df_final[["id", "nom_complet_x", "grade", "jour", "seance"]]
    df_final = df_final.rename(columns={"nom_complet_x": "nom_complet"})

    return df_final
