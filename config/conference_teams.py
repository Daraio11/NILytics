"""
Conference and team reference data for NILytics.
Maps every FBS/FCS team to conference and market tier (P4/G6/FCS).

Power 4 (P4): SEC, Big Ten, Big 12, ACC
Group of 6 (G6): AAC, Sun Belt, MAC, MW, C-USA, Independent (non-P4)
FCS: All FCS conferences
"""

CONFERENCE_TEAMS = {
    # ============================================================
    # SEC (P4)
    # ============================================================
    "ALABAMA": ("SEC", "P4"),
    "ARKANSAS": ("SEC", "P4"),
    "AUBURN": ("SEC", "P4"),
    "FLORIDA": ("SEC", "P4"),
    "GEORGIA": ("SEC", "P4"),
    "KENTUCKY": ("SEC", "P4"),
    "LSU": ("SEC", "P4"),
    "MISS STATE": ("SEC", "P4"),
    "MISSISSIPPI ST": ("SEC", "P4"),
    "MISSOURI": ("SEC", "P4"),
    "OKLAHOMA": ("SEC", "P4"),
    "OLE MISS": ("SEC", "P4"),
    "SOUTH CAROLINA": ("SEC", "P4"),
    "S CAROLINA": ("SEC", "P4"),
    "TENNESSEE": ("SEC", "P4"),
    "TEXAS": ("SEC", "P4"),
    "TEXAS A&M": ("SEC", "P4"),
    "VANDERBILT": ("SEC", "P4"),

    # ============================================================
    # Big Ten (P4)
    # ============================================================
    "ILLINOIS": ("Big Ten", "P4"),
    "INDIANA": ("Big Ten", "P4"),
    "IOWA": ("Big Ten", "P4"),
    "MARYLAND": ("Big Ten", "P4"),
    "MICHIGAN": ("Big Ten", "P4"),
    "MICHIGAN ST": ("Big Ten", "P4"),
    "MICHIGAN STATE": ("Big Ten", "P4"),
    "MINNESOTA": ("Big Ten", "P4"),
    "NEBRASKA": ("Big Ten", "P4"),
    "NORTHWESTERN": ("Big Ten", "P4"),
    "NWESTERN": ("Big Ten", "P4"),
    "OHIO STATE": ("Big Ten", "P4"),
    "OHIO ST": ("Big Ten", "P4"),
    "OREGON": ("Big Ten", "P4"),
    "PENN STATE": ("Big Ten", "P4"),
    "PENN ST": ("Big Ten", "P4"),
    "PURDUE": ("Big Ten", "P4"),
    "RUTGERS": ("Big Ten", "P4"),
    "USC": ("Big Ten", "P4"),
    "UCLA": ("Big Ten", "P4"),
    "WASHINGTON": ("Big Ten", "P4"),
    "WISCONSIN": ("Big Ten", "P4"),

    # ============================================================
    # Big 12 (P4)
    # ============================================================
    "ARIZONA": ("Big 12", "P4"),
    "ARIZONA ST": ("Big 12", "P4"),
    "ARIZONA STATE": ("Big 12", "P4"),
    "BAYLOR": ("Big 12", "P4"),
    "BYU": ("Big 12", "P4"),
    "BRIGHAM YOUNG": ("Big 12", "P4"),
    "CENTRAL FLORIDA": ("Big 12", "P4"),
    "UCF": ("Big 12", "P4"),
    "CINCINNATI": ("Big 12", "P4"),
    "COLORADO": ("Big 12", "P4"),
    "HOUSTON": ("Big 12", "P4"),
    "IOWA STATE": ("Big 12", "P4"),
    "IOWA ST": ("Big 12", "P4"),
    "KANSAS": ("Big 12", "P4"),
    "KANSAS STATE": ("Big 12", "P4"),
    "KANSAS ST": ("Big 12", "P4"),
    "OKLAHOMA STATE": ("Big 12", "P4"),
    "OKLAHOMA ST": ("Big 12", "P4"),
    "TCU": ("Big 12", "P4"),
    "TEXAS TECH": ("Big 12", "P4"),
    "UTAH": ("Big 12", "P4"),
    "WEST VIRGINIA": ("Big 12", "P4"),
    "W VIRGINIA": ("Big 12", "P4"),

    # ============================================================
    # ACC (P4)
    # ============================================================
    "BOSTON COLLEGE": ("ACC", "P4"),
    "CALIFORNIA": ("ACC", "P4"),
    "CAL": ("ACC", "P4"),
    "CLEMSON": ("ACC", "P4"),
    "DUKE": ("ACC", "P4"),
    "FLORIDA STATE": ("ACC", "P4"),
    "FLORIDA ST": ("ACC", "P4"),
    "GEORGIA TECH": ("ACC", "P4"),
    "GA TECH": ("ACC", "P4"),
    "LOUISVILLE": ("ACC", "P4"),
    "MIAMI": ("ACC", "P4"),
    "MIAMI (FL)": ("ACC", "P4"),
    "NORTH CAROLINA": ("ACC", "P4"),
    "N CAROLINA": ("ACC", "P4"),
    "UNC": ("ACC", "P4"),
    "NC STATE": ("ACC", "P4"),
    "PITTSBURGH": ("ACC", "P4"),
    "PITT": ("ACC", "P4"),
    "SMU": ("ACC", "P4"),
    "STANFORD": ("ACC", "P4"),
    "SYRACUSE": ("ACC", "P4"),
    "VIRGINIA": ("ACC", "P4"),
    "VIRGINIA TECH": ("ACC", "P4"),
    "VA TECH": ("ACC", "P4"),
    "WAKE FOREST": ("ACC", "P4"),

    # ============================================================
    # AAC (G6)
    # ============================================================
    "ARMY": ("AAC", "G6"),
    "CHARLOTTE": ("AAC", "G6"),
    "EAST CAROLINA": ("AAC", "G6"),
    "E CAROLINA": ("AAC", "G6"),
    "ECU": ("AAC", "G6"),
    "FAU": ("AAC", "G6"),
    "FLORIDA ATLANTIC": ("AAC", "G6"),
    "MEMPHIS": ("AAC", "G6"),
    "NAVY": ("AAC", "G6"),
    "NORTH TEXAS": ("AAC", "G6"),
    "N TEXAS": ("AAC", "G6"),
    "RICE": ("AAC", "G6"),
    "SOUTH FLORIDA": ("AAC", "G6"),
    "USF": ("AAC", "G6"),
    "TEMPLE": ("AAC", "G6"),
    "TULANE": ("AAC", "G6"),
    "TULSA": ("AAC", "G6"),
    "UAB": ("AAC", "G6"),
    "UTSA": ("AAC", "G6"),

    # ============================================================
    # Sun Belt (G6)
    # ============================================================
    "APPALACHIAN ST": ("Sun Belt", "G6"),
    "APPALACHIAN STATE": ("Sun Belt", "G6"),
    "APP STATE": ("Sun Belt", "G6"),
    "ARKANSAS STATE": ("Sun Belt", "G6"),
    "ARK STATE": ("Sun Belt", "G6"),
    "COASTAL CAROLINA": ("Sun Belt", "G6"),
    "COASTAL CAR": ("Sun Belt", "G6"),
    "GEORGIA SOUTHERN": ("Sun Belt", "G6"),
    "GA SOUTHERN": ("Sun Belt", "G6"),
    "GEORGIA STATE": ("Sun Belt", "G6"),
    "GA STATE": ("Sun Belt", "G6"),
    "JAMES MADISON": ("Sun Belt", "G6"),
    "LOUISIANA": ("Sun Belt", "G6"),
    "UL LAFAYETTE": ("Sun Belt", "G6"),
    "LOUISIANA LAFAYETTE": ("Sun Belt", "G6"),
    "UL MONROE": ("Sun Belt", "G6"),
    "LOUISIANA MONROE": ("Sun Belt", "G6"),
    "MARSHALL": ("Sun Belt", "G6"),
    "OLD DOMINION": ("Sun Belt", "G6"),
    "SOUTH ALABAMA": ("Sun Belt", "G6"),
    "S ALABAMA": ("Sun Belt", "G6"),
    "SOUTHERN MISS": ("Sun Belt", "G6"),
    "S MISSISSIPPI": ("Sun Belt", "G6"),
    "TEXAS STATE": ("Sun Belt", "G6"),
    "TROY": ("Sun Belt", "G6"),

    # ============================================================
    # MAC (G6)
    # ============================================================
    "AKRON": ("MAC", "G6"),
    "BALL STATE": ("MAC", "G6"),
    "BALL ST": ("MAC", "G6"),
    "BOWLING GREEN": ("MAC", "G6"),
    "BUFFALO": ("MAC", "G6"),
    "CENTRAL MICHIGAN": ("MAC", "G6"),
    "C MICHIGAN": ("MAC", "G6"),
    "EASTERN MICHIGAN": ("MAC", "G6"),
    "E MICHIGAN": ("MAC", "G6"),
    "KENT STATE": ("MAC", "G6"),
    "KENT ST": ("MAC", "G6"),
    "MIAMI (OH)": ("MAC", "G6"),
    "MIAMI OHIO": ("MAC", "G6"),
    "NORTHERN ILLINOIS": ("MAC", "G6"),
    "N ILLINOIS": ("MAC", "G6"),
    "NIU": ("MAC", "G6"),
    "OHIO": ("MAC", "G6"),
    "TOLEDO": ("MAC", "G6"),
    "WESTERN MICHIGAN": ("MAC", "G6"),
    "W MICHIGAN": ("MAC", "G6"),

    # ============================================================
    # Mountain West (G6)
    # ============================================================
    "AIR FORCE": ("MW", "G6"),
    "BOISE STATE": ("MW", "G6"),
    "BOISE ST": ("MW", "G6"),
    "COLORADO STATE": ("MW", "G6"),
    "COLORADO ST": ("MW", "G6"),
    "FRESNO STATE": ("MW", "G6"),
    "FRESNO ST": ("MW", "G6"),
    "HAWAII": ("MW", "G6"),
    "NEVADA": ("MW", "G6"),
    "NEW MEXICO": ("MW", "G6"),
    "SAN DIEGO STATE": ("MW", "G6"),
    "SAN DIEGO ST": ("MW", "G6"),
    "SAN JOSE STATE": ("MW", "G6"),
    "SAN JOSE ST": ("MW", "G6"),
    "UNLV": ("MW", "G6"),
    "UTAH STATE": ("MW", "G6"),
    "UTAH ST": ("MW", "G6"),
    "WYOMING": ("MW", "G6"),

    # ============================================================
    # C-USA (G6)
    # ============================================================
    "FIU": ("C-USA", "G6"),
    "JACKSONVILLE STATE": ("C-USA", "G6"),
    "JACKSONVILLE ST": ("C-USA", "G6"),
    "KENNESAW STATE": ("C-USA", "G6"),
    "KENNESAW ST": ("C-USA", "G6"),
    "LIBERTY": ("C-USA", "G6"),
    "LOUISIANA TECH": ("C-USA", "G6"),
    "LA TECH": ("C-USA", "G6"),
    "MIDDLE TENNESSEE": ("C-USA", "G6"),
    "MIDDLE TENN": ("C-USA", "G6"),
    "MTSU": ("C-USA", "G6"),
    "NEW MEXICO STATE": ("C-USA", "G6"),
    "NEW MEXICO ST": ("C-USA", "G6"),
    "SAM HOUSTON": ("C-USA", "G6"),
    "SAM HOUSTON STATE": ("C-USA", "G6"),
    "SAM HOUSTON ST": ("C-USA", "G6"),
    "UTEP": ("C-USA", "G6"),
    "WESTERN KENTUCKY": ("C-USA", "G6"),
    "W KENTUCKY": ("C-USA", "G6"),

    # ============================================================
    # Independents — FBS (G6 default)
    # ============================================================
    "NOTRE DAME": ("Ind", "P4"),  # Notre Dame is P4-tier
    "UCONN": ("Ind", "G6"),
    "CONNECTICUT": ("Ind", "G6"),
    "UMASS": ("Ind", "G6"),
    "MASSACHUSETTS": ("Ind", "G6"),

    # ============================================================
    # FCS (common teams that appear in PFF data)
    # ============================================================
    "NORTH DAKOTA STATE": ("MVFC", "FCS"),
    "NORTH DAKOTA ST": ("MVFC", "FCS"),
    "NDSU": ("MVFC", "FCS"),
    "SOUTH DAKOTA STATE": ("MVFC", "FCS"),
    "SOUTH DAKOTA ST": ("MVFC", "FCS"),
    "SDSU": ("MVFC", "FCS"),
    "MONTANA": ("Big Sky", "FCS"),
    "MONTANA STATE": ("Big Sky", "FCS"),
    "MONTANA ST": ("Big Sky", "FCS"),
    "SACRAMENTO STATE": ("Big Sky", "FCS"),
    "SACRAMENTO ST": ("Big Sky", "FCS"),
    "WEBER STATE": ("Big Sky", "FCS"),
    "WEBER ST": ("Big Sky", "FCS"),
    "VILLANOVA": ("CAA", "FCS"),
    "JAMES MADISON": ("Sun Belt", "G6"),  # JMU moved to FBS
    "DELAWARE": ("CAA", "FCS"),
    "RICHMOND": ("CAA", "FCS"),
    "WILLIAM & MARY": ("CAA", "FCS"),
    "TOWSON": ("CAA", "FCS"),
    "MAINE": ("CAA", "FCS"),
    "NEW HAMPSHIRE": ("CAA", "FCS"),
    "STONY BROOK": ("CAA", "FCS"),
    "RHODE ISLAND": ("CAA", "FCS"),
    "ELON": ("CAA", "FCS"),
    "ALBANY": ("CAA", "FCS"),
    "YOUNGSTOWN STATE": ("MVFC", "FCS"),
    "YOUNGSTOWN ST": ("MVFC", "FCS"),
    "ILLINOIS STATE": ("MVFC", "FCS"),
    "ILLINOIS ST": ("MVFC", "FCS"),
    "INDIANA STATE": ("MVFC", "FCS"),
    "INDIANA ST": ("MVFC", "FCS"),
    "MISSOURI STATE": ("MVFC", "FCS"),
    "MISSOURI ST": ("MVFC", "FCS"),
    "NORTHERN IOWA": ("MVFC", "FCS"),
    "N IOWA": ("MVFC", "FCS"),
    "SOUTH DAKOTA": ("MVFC", "FCS"),
    "NORTH DAKOTA": ("MVFC", "FCS"),
    "WESTERN ILLINOIS": ("MVFC", "FCS"),
    "W ILLINOIS": ("MVFC", "FCS"),
    "EASTERN WASHINGTON": ("Big Sky", "FCS"),
    "E WASHINGTON": ("Big Sky", "FCS"),
    "IDAHO": ("Big Sky", "FCS"),
    "PORTLAND STATE": ("Big Sky", "FCS"),
    "PORTLAND ST": ("Big Sky", "FCS"),
    "NORTHERN ARIZONA": ("Big Sky", "FCS"),
    "N ARIZONA": ("Big Sky", "FCS"),
    "CAL POLY": ("Big Sky", "FCS"),
    "UC DAVIS": ("Big Sky", "FCS"),
    "SOUTHERN UTAH": ("Big Sky", "FCS"),
    "S UTAH": ("Big Sky", "FCS"),
    "JACKSON STATE": ("SWAC", "FCS"),
    "JACKSON ST": ("SWAC", "FCS"),
    "ALCORN STATE": ("SWAC", "FCS"),
    "ALCORN ST": ("SWAC", "FCS"),
    "GRAMBLING": ("SWAC", "FCS"),
    "FLORIDA A&M": ("SWAC", "FCS"),
    "BETHUNE-COOKMAN": ("SWAC", "FCS"),
    "SOUTHERN": ("SWAC", "FCS"),
    "CHATTANOOGA": ("SoCon", "FCS"),
    "FURMAN": ("SoCon", "FCS"),
    "MERCER": ("SoCon", "FCS"),
    "SAMFORD": ("SoCon", "FCS"),
    "WOFFORD": ("SoCon", "FCS"),
    "ETSU": ("SoCon", "FCS"),
    "EAST TENN STATE": ("SoCon", "FCS"),
    "CITADEL": ("SoCon", "FCS"),
    "THE CITADEL": ("SoCon", "FCS"),
    "VMI": ("SoCon", "FCS"),
    "WESTERN CAROLINA": ("SoCon", "FCS"),
    "W CAROLINA": ("SoCon", "FCS"),
    "HARVARD": ("Ivy", "FCS"),
    "YALE": ("Ivy", "FCS"),
    "PRINCETON": ("Ivy", "FCS"),
    "DARTMOUTH": ("Ivy", "FCS"),
    "COLUMBIA": ("Ivy", "FCS"),
    "CORNELL": ("Ivy", "FCS"),
    "BROWN": ("Ivy", "FCS"),
    "PENN": ("Ivy", "FCS"),
    "HOLY CROSS": ("Patriot", "FCS"),
    "LEHIGH": ("Patriot", "FCS"),
    "LAFAYETTE": ("Patriot", "FCS"),
    "COLGATE": ("Patriot", "FCS"),
    "BUCKNELL": ("Patriot", "FCS"),
    "FORDHAM": ("Patriot", "FCS"),
    "GEORGETOWN": ("Patriot", "FCS"),
    "SOUTHEASTERN LOUISIANA": ("Southland", "FCS"),
    "SE LOUISIANA": ("Southland", "FCS"),
    "NICHOLLS": ("Southland", "FCS"),
    "NICHOLLS STATE": ("Southland", "FCS"),
    "NICHOLLS ST": ("Southland", "FCS"),
    "MCNEESE": ("Southland", "FCS"),
    "MCNEESE STATE": ("Southland", "FCS"),
    "NORTHWESTERN STATE": ("Southland", "FCS"),
    "NW STATE": ("Southland", "FCS"),
    "HOUSTON BAPTIST": ("Southland", "FCS"),
    "HOUSTON CHRISTIAN": ("Southland", "FCS"),
    "INCARNATE WORD": ("Southland", "FCS"),
    "LAMAR": ("Southland", "FCS"),
    "CENTRAL ARKANSAS": ("Southland", "FCS"),
    "C ARKANSAS": ("Southland", "FCS"),
    "ABILENE CHRISTIAN": ("WAC", "FCS"),
    "STEPHEN F AUSTIN": ("Southland", "FCS"),
    "SFA": ("Southland", "FCS"),
    "TARLETON STATE": ("WAC", "FCS"),
    "TARLETON ST": ("WAC", "FCS"),
    "EASTERN KENTUCKY": ("ASUN", "FCS"),
    "E KENTUCKY": ("ASUN", "FCS"),
    "CENTRAL CONNECTICUT": ("NEC", "FCS"),
    "C CONNECTICUT": ("NEC", "FCS"),
    "CCSU": ("NEC", "FCS"),
    "WAGNER": ("NEC", "FCS"),
    "SACRED HEART": ("NEC", "FCS"),
    "DUQUESNE": ("NEC", "FCS"),
    "LONG ISLAND": ("NEC", "FCS"),
    "LIU": ("NEC", "FCS"),
    "ROBERT MORRIS": ("NEC", "FCS"),
    "MERRIMACK": ("NEC", "FCS"),
    "WASH STATE": ("Ind", "P4"),  # Pac-12 remnant, P4 tier
    "OREGON STATE": ("Ind", "P4"),
    "OREGON ST": ("Ind", "P4"),
}

# PFF position code -> NILytics position mapping
PFF_POSITION_MAP = {
    "QB": "QB",
    "HB": "RB",
    "WR": "WR",
    "TE": "TE",
    "T": "OT",
    "C": "IOL",
    "G": "IOL",
    "ED": "EDGE",
    "DI": "IDL",
    "LB": "LB",
    "CB": "CB",
    "S": "S",
}

# Positions we exclude from valuation
EXCLUDED_POSITIONS = {"FB", "K", "P", "LS"}


def get_team_info(team_name: str) -> tuple:
    """Returns (conference, market) for a team, or ('Unknown', 'FCS') as fallback."""
    upper = team_name.strip().upper()
    if upper in CONFERENCE_TEAMS:
        return CONFERENCE_TEAMS[upper]
    # Default unknown teams to FCS
    return ("Unknown", "FCS")


def get_nilytics_position(pff_position: str) -> str | None:
    """Maps PFF position code to NILytics position. Returns None for excluded positions."""
    if not pff_position:
        return None
    pos = pff_position.strip().upper()
    if pos in EXCLUDED_POSITIONS:
        return None
    return PFF_POSITION_MAP.get(pos)
