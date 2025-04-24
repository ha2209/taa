import pandas as pd
import streamlit as st


def display_asset_allocations(df, profiles, show_active_weights, highlight_level_1=False):
    """
    Displays asset allocation data in a styled format, with optional highlighting and active weight calculations.

    Args:
        df (pd.DataFrame): The dataframe containing asset allocation data.
        profiles (list): A list of profiles to calculate differences for, if active weights are enabled.
        show_active_weights (bool): If True, calculates and displays active weights by adding difference columns.
        highlight_level_1 (bool, optional): If True, highlights specific rows ('Stocks', 'Bonds', 'Cash') 
            with bold font and a dark blue background. Defaults to False.

    Behavior:
        - If `show_active_weights` is True:
            - Adds difference columns to the dataframe for the specified profiles.
            - Displays the dataframe with active weights and optional highlights.
        - If `show_active_weights` is False:
            - Displays the dataframe without active weights.
            - Applies optional row-level highlighting if `highlight_level_1` is True.

    Note:
        - The function uses Streamlit's `st.dataframe` for rendering the dataframe.
        - Styling is applied using pandas' Styler and custom CSS.

    """
    if show_active_weights:
        # Add difference columns for each profile
        df = add_difference_column(df, profiles)
        # Display the dataframe with active weights
        display_allocation_with_highlights(df, highlight_level_1=highlight_level_1)
    else:
        # Display the dataframe without active weights
        df_style = df.style.format(precision=1)
        if highlight_level_1:
            st.dataframe(
                df_style.applymap(lambda _: 'font-weight: bold; background-color: #00008B; color: white;', subset=pd.IndexSlice[['Stocks', 'Bonds', 'Cash'], :]),
                use_container_width=True
            )
        else:
            st.dataframe(df_style, use_container_width=True)



def add_difference_column(df, profiles, col1_label="Strategic", col2_label="Tactical", diff_label="Difference"):
    """
    Adds a difference column (col2 - col1) to the DataFrame for each profile
    and reorders columns to intersperse col1, col2, and the difference column.

    Args:
        df (pd.DataFrame): DataFrame containing col1 and col2 columns.
        profiles (list): List of profile names.
        col1_label (str): Label for the first column (e.g., 'Strategic').
        col2_label (str): Label for the second column (e.g., 'Tactical').
        diff_label (str): Label for the difference column (e.g., 'Tactical - Strategic').

    Returns:
        pd.DataFrame: Updated DataFrame with the difference columns added and reordered.
    """
    # Compute the difference for each profile
    difference = df.xs(col2_label, level='Type', axis=1) - df.xs(col1_label, level='Type', axis=1)
    # Add the difference columns next to col2 under each profile
    for profile in profiles:
        df[(profile, diff_label)] = difference[profile]
    # Reorder columns to intersperse col1, col2, and the difference column
    new_columns = []
    for profile in profiles:
        new_columns.extend([(profile, col1_label), (profile, col2_label), (profile, diff_label)])
    return df[new_columns]


def display_allocation_with_highlights(df, precision=1, highlight_level_1=False):
    """
    Displays a styled dataframe with highlighted differences.

    Args:
        df (pd.DataFrame): The dataframe to display.
        precision (int): Decimal precision for formatting.
        highlight_level_1 (bool): Whether to highlight level 1 allocations (Stocks, Bonds, Cash).

    Returns:
        None
    """
    df_style = df.style.format(precision=precision).applymap(
        lambda val: (
            f'background-color: rgba(0, 255, 0, {min(1, abs(val) / 10)}); color: white;' if val > 0 else
            f'background-color: rgba(255, 0, 0, {min(1, abs(val) / 10)}); color: white;' if val < 0 else ''
        ),
        subset=pd.IndexSlice[:, pd.IndexSlice[:, 'Difference']]
    )
    if highlight_level_1:
        st.dataframe(
            df_style.applymap(lambda _: 'font-weight: bold; background-color: #00008B; color: white;', subset=pd.IndexSlice[['Stocks', 'Bonds', 'Cash'], :]),
            use_container_width=True
        )
    else:
        st.dataframe(df_style, use_container_width=True)