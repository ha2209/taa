import streamlit as st
import pandas as pd
import json
from utils import display_asset_allocations


def load_config(file_path="config.json"):
    """
    Load configuration data from a JSON file.

    Args:
        file_path (str): The path to the JSON configuration file. Defaults to "config.json".

    Returns:
        dict: The configuration data loaded from the file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file is not a valid JSON.
    """
    with open(file_path) as f:
        return json.load(f)


def compute_tactical_allocations(strategic_allocations, multipliers, profiles, active_weights):
    """
    Computes tactical allocations for a set of assets based on strategic allocations,
    multipliers, profiles, and active weights.

    Args:
        strategic_allocations (dict): A dictionary where keys are asset names and values
            are lists of strategic allocation values for each profile.
        multipliers (dict): A dictionary where keys are profile names and values are
            multipliers to adjust the allocations.
        profiles (list): A list of profile names corresponding to the order of allocations
            in the strategic_allocations values.
        active_weights (dict): A dictionary where keys are asset names (in lowercase and
            with spaces replaced by underscores) and values are the active weights for
            those assets.

    Returns:
        dict: A dictionary where keys are asset names and values are lists of computed
        tactical allocations for each profile.
    """
    return {
        asset: [
            strategic_allocations[asset][i] + multipliers[p] * active_weights[asset.lower().replace(" ", "_")]
            for i, p in enumerate(profiles)
        ]
        for asset in strategic_allocations.keys()
    }


def display_level_1_allocations(strategic_allocations, tactical_allocations, profiles, show_active_weights):
    """
    Generates and displays a DataFrame of level 1 asset allocations based on strategic and tactical allocations.

    This function processes the given strategic and tactical allocations for various profiles, organizes the data
    into a structured DataFrame, and displays the asset allocations using the `display_asset_allocations` function.

    Args:
        strategic_allocations (dict): A dictionary where keys are asset names and values are lists of strategic 
            allocation values corresponding to each profile.
        tactical_allocations (dict): A dictionary where keys are asset names and values are lists of tactical 
            allocation values corresponding to each profile.
        profiles (list): A list of profile names corresponding to the allocation data.
        show_active_weights (bool): A flag indicating whether to display active weights in the allocation display.

    Returns:
        pd.DataFrame: A DataFrame containing the level 1 asset allocations with a MultiIndex for columns 
        (Profile, Type), where "Type" can be "Strategic" or "Tactical".
    """
    level_1_data = {}
    for asset in strategic_allocations.keys():
        for profile, strategic, tactical in zip(profiles, strategic_allocations[asset], tactical_allocations[asset]):
            level_1_data[(profile, 'Strategic')] = level_1_data.get((profile, 'Strategic'), []) + [strategic]
            level_1_data[(profile, 'Tactical')] = level_1_data.get((profile, 'Tactical'), []) + [tactical]

    level_1_allocation_df = pd.DataFrame(level_1_data, index=strategic_allocations.keys())
    level_1_allocation_df.columns = pd.MultiIndex.from_tuples(level_1_allocation_df.columns, names=["Profile", "Type"])
    display_asset_allocations(level_1_allocation_df, profiles, show_active_weights)
    return level_1_allocation_df


def input_active_weights(default_weights, title, min_value=-10.0, max_value=10.0, step=1.0):
    """
    Displays a Streamlit interface for adjusting active weights and validates their sum.

    Parameters:
        default_weights (dict): A dictionary where keys are column names and values are the default active weights.
        title (str): The title to display above the sliders in the Streamlit interface.
        min_value (float, optional): The minimum value for the sliders. Defaults to -10.0.
        max_value (float, optional): The maximum value for the sliders. Defaults to 10.0.
        step (float, optional): The step size for the sliders. Defaults to 1.0.

    Returns:
        dict: A dictionary of adjusted active weights where keys are column names and values are the updated weights.

    Notes:
        - The function uses Streamlit to create sliders for each column in the `default_weights` dictionary.
        - It ensures that the sum of all active weights equals 0. If not, an error message is displayed.
        - If the sum is valid, a success message is displayed.
    """
    st.subheader(title)
    active_weights_df = pd.DataFrame(default_weights, index=['Active Weight (%)'])
    for col in active_weights_df.columns:
        active_weights_df.at['Active Weight (%)', col] = st.slider(
            f"{col}",
            min_value=min_value,
            max_value=max_value,
            value=active_weights_df.at['Active Weight (%)', col],
            step=step
        )
    if active_weights_df.sum(axis=1).values[0] != 0:
        st.error("The sum of active weights must equal 0. Please adjust the weights.")
    else:
        st.success("The sum of active weights is valid.")
    return active_weights_df.iloc[0].to_dict()


def compute_level_2_tactical_allocations(base_allocations, active_weights):
    """
    Computes level 2 tactical allocations by combining base allocations 
    with active weights.

    Args:
        base_allocations (dict): A dictionary where keys represent asset 
            categories and values represent the base allocation percentages 
            or amounts.
        active_weights (dict): A dictionary where keys represent asset 
            categories and values represent the active weight adjustments 
            to be applied to the base allocations.

    Returns:
        dict: A dictionary containing the updated allocations for each 
        asset category, calculated as the sum of the base allocations 
        and the active weights.

    Raises:
        KeyError: If a key in `active_weights` does not exist in 
        `base_allocations`.
    """
    return {
        key: base_allocations[key] + active_weights[key]
        for key in base_allocations.keys()
    }


def display_level_2_allocations(equities_size_style, fixed_income_sector, tactical_equities, tactical_fixed_income):
    """
    Displays and returns dataframes for level 2 allocations of equities and fixed income.

    This function creates two columns in a Streamlit app to display the strategic and tactical
    allocations for equities (size and style) and fixed income (sector). It also returns the
    corresponding dataframes for further use.

    Args:
        equities_size_style (dict): A dictionary containing strategic allocations for equities
            based on size and style.
        fixed_income_sector (dict): A dictionary containing strategic allocations for fixed
            income based on sector.
        tactical_equities (dict): A dictionary containing tactical allocations for equities
            based on size and style.
        tactical_fixed_income (dict): A dictionary containing tactical allocations for fixed
            income based on sector.

    Returns:
        tuple: A tuple containing two pandas DataFrames:
            - equities_df: DataFrame with strategic and tactical allocations for equities.
            - fixed_income_df: DataFrame with strategic and tactical allocations for fixed income.
    """
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Equities size and style allocations")
        equities_df = pd.DataFrame(
            {'Strategic': equities_size_style, 'Tactical': tactical_equities},
            index=equities_size_style.keys()
        )
        st.dataframe(equities_df, use_container_width=True)
    with col2:
        st.subheader("Fixed Income sector allocations")
        fixed_income_df = pd.DataFrame(
            {'Strategic': fixed_income_sector, 'Tactical': tactical_fixed_income},
            index=fixed_income_sector.keys()
        )
        st.dataframe(fixed_income_df, use_container_width=True)
    return equities_df, fixed_income_df


def compute_total_allocations(level_1_df, equities_df, fixed_income_df, strategic_allocations):
    """
    Computes the total allocations for various asset classes, including equities, fixed income, 
    and cash, based on the provided level 1 allocations, equities breakdown, fixed income breakdown, 
    and strategic allocations.

    Args:
        level_1_df (pd.DataFrame): A DataFrame containing level 1 asset class allocations 
            (e.g., 'Equities', 'Fixed Income', 'Cash') with columns representing allocation types 
            (e.g., 'Strategic', 'Tactical').
        equities_df (pd.DataFrame): A DataFrame containing level 2 breakdown of equities 
            with rows as asset classes (e.g., 'Large Cap', 'Small Cap') and columns for allocation 
            types (e.g., 'Strategic', 'Tactical').
        fixed_income_df (pd.DataFrame): A DataFrame containing level 2 breakdown of fixed income 
            with rows as asset classes (e.g., 'Government Bonds', 'Corporate Bonds') and columns 
            for allocation types (e.g., 'Strategic', 'Tactical').
        strategic_allocations (dict): A dictionary where keys are level 1 asset classes 
            (e.g., 'Equities', 'Fixed Income', 'Cash') and values are their respective strategic 
            allocation percentages.

    Returns:
        pd.DataFrame: A DataFrame containing the total allocations for all asset classes, 
        including level 1 and level 2 breakdowns, with rows as asset classes and columns 
        representing allocation types (e.g., 'Strategic', 'Tactical').
    """
    idx = ['Equities'] + equities_df.index.to_list() + ['Fixed Income'] + fixed_income_df.index.to_list() + ['Cash']
    cols = level_1_df.columns
    df_total_allocations = pd.DataFrame(index=idx, columns=cols)
    for lvl1_asset_class in strategic_allocations.keys():
        df_total_allocations.loc[lvl1_asset_class] = level_1_df.loc[lvl1_asset_class]
    for lvl2_asset_class in equities_df.index:
        for typ in ['Strategic', 'Tactical']:
            df_total_allocations.loc[lvl2_asset_class, pd.IndexSlice[:, typ]] = (
                equities_df.loc[lvl2_asset_class, typ] * df_total_allocations.loc['Equities', pd.IndexSlice[:, typ]] / 100
            )
    for lvl2_asset_class in fixed_income_df.index:
        for typ in ['Strategic', 'Tactical']:
            df_total_allocations.loc[lvl2_asset_class, pd.IndexSlice[:, typ]] = (
                fixed_income_df.loc[lvl2_asset_class, typ] * df_total_allocations.loc['Fixed Income', pd.IndexSlice[:, typ]] / 100
            )
    return df_total_allocations


def main():
    st.set_page_config(layout="wide")
    st.title("Asset Allocation Dashboard")
    show_active_weights = st.toggle(label="Show Active Weights", value=False)

    config = load_config()

    # Inputs
    multipliers = config["multipliers"]
    profiles = list(multipliers.keys())
    strategic_allocations = config["strategic_allocations"]
    equities_size_style = config["equities_size_style"]
    fixed_income_sector = config["fixed_income_sector"]

    moderate_active_weight = {
        'equities': st.number_input(
            "Moderate Profile: Active Equities Weight (%)",
            min_value=-10.0, max_value=10.0,
            value=config["moderate_equities_active"], step=1.0
        )
    }
    moderate_active_weight['fixed_income'] = -1. * moderate_active_weight['equities']
    moderate_active_weight['cash'] = 0.0

    # Compute Tactical allocations
    tactical_allocations = compute_tactical_allocations(
        strategic_allocations, multipliers, profiles, moderate_active_weight
    )

    # Display Level 1 Allocations
    level_1_allocation_df = display_level_1_allocations(
        strategic_allocations, tactical_allocations, profiles, show_active_weights
    )

    # Input Level 2 Active Weights
    st.subheader("Input Level 2 Active Weights")
    col1, col2 = st.columns(2)
    with col1:
        equities_style_active = input_active_weights(config["default_equities_active_weight"], "Equities (%)")
    with col2:
        fixed_income_sector_active = input_active_weights(config["default_fixed_income_active_weight"], "Fixed Income (%)")

    # Compute Level 2 Tactical Allocations
    tactical_equities_size_style = compute_level_2_tactical_allocations(equities_size_style, equities_style_active)
    tactical_fixed_income_sector = compute_level_2_tactical_allocations(fixed_income_sector, fixed_income_sector_active)

    # Display Level 2 Allocations
    equities_df, fixed_income_df = display_level_2_allocations(
        equities_size_style, fixed_income_sector, tactical_equities_size_style, tactical_fixed_income_sector
    )

    # Compute Total Allocations
    df_total_allocations = compute_total_allocations(
        level_1_allocation_df, equities_df, fixed_income_df, strategic_allocations
    )

    # Display Total Allocations
    st.subheader("Total allocations")
    display_asset_allocations(df_total_allocations, profiles, show_active_weights, highlight_level_1=True)


if __name__ == "__main__":
    main()