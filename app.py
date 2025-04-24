import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")

st.title("Asset Allocation Dashboard")

# Load config.json
with open("config.json") as f:
    config = json.load(f)

# --- Inputs ---
moderate_stock_active = st.number_input("Moderate Profile: Active Stock Weight (%)", min_value=-10.0, max_value=10.0, value=config["moderate_stock_active"], step=1.0)

# Multipliers for different profiles
multipliers = config["multipliers"]
profiles = list(multipliers.keys())

# Strategic allocations (Table 7 - Tier 0 Liquidity)
strategic_allocations = config["strategic_allocations"]
# Stocks size and style total allocations
stocks_size_style = config["stocks_size_style"]
# Bonds sector total allocations
bonds_sector = config["bonds_sector"]


# Compute Tactical allocations using active weights
tactical_allocations = {
    'Stocks': [strategic_allocations['Stocks'][i] + multipliers[p] * moderate_stock_active for i, p in enumerate(profiles)],
    'Bonds': [strategic_allocations['Bonds'][i] - multipliers[p] * moderate_stock_active for i, p in enumerate(profiles)],
    'Cash': strategic_allocations['Cash']  # unchanged
}

# Display Strategic and Tactical without alternatives
st.subheader("Strategic and Tactical allocations without alternative assets (Tier 0 liquidity)")
level_1_data = {}
for asset in ['Stocks', 'Bonds', 'Cash']:
    for profile, strategic, tactical in zip(profiles, strategic_allocations[asset], tactical_allocations[asset]):
        level_1_data[(profile, 'Strategic')] = level_1_data.get((profile, 'Strategic'), []) + [strategic]
        level_1_data[(profile, 'Tactical')] = level_1_data.get((profile, 'Tactical'), []) + [tactical]

level_1_allocation_df = pd.DataFrame(level_1_data, index=['Stocks', 'Bonds', 'Cash'])
level_1_allocation_df.columns = pd.MultiIndex.from_tuples(level_1_allocation_df.columns, names=["Profile", "Type"])
st.dataframe(level_1_allocation_df, use_container_width=True)

# Stock style and size active weights
stock_style_active = {}
st.subheader("Input Stocks and Bonds Active Weights")
# Initialize stock style active weights with default values
default_stocks_active_weight = config["default_stocks_active_weight"]
# Initialize bond sector active weights with default values
default_bonds_active_weight = config["default_bonds_active_weight"]

# Create an editable table for stock style and bonds secor active weights
stock_style_active_df = pd.DataFrame(default_stocks_active_weight, index=['Active Weight (%)'])
bond_sector_active_df = pd.DataFrame(default_bonds_active_weight, index=['Active Weight (%)'])
col1, col2 = st.columns(2)

with col1:
    for style in stock_style_active_df.columns:
        stock_style_active_df.at['Active Weight (%)', style] = st.slider(
            f"{style} Active Weight (%)",
            min_value=-10.0,
            max_value=10.0,
            value=stock_style_active_df.at['Active Weight (%)', style],
            step=1.0
        )
    # Assert that the sum of active weights is 0
    if stock_style_active_df.sum(axis=1).values[0] != 0:
        st.error("The sum of active weights must equal 0. Please adjust the weights.")
    else:
        st.success("The sum of active weights is valid.")
    # Convert the active weights to a dictionary
    stock_style_active = stock_style_active_df.iloc[0].to_dict()

with col2:
    bond_sector_active_df = pd.DataFrame(bond_sector_active_df, index=['Active Weight (%)'])
    for sector in bond_sector_active_df.columns:
        bond_sector_active_df.at['Active Weight (%)', sector] = st.slider(
            f"{sector} Active Weight (%)",
            min_value=-10.0,
            max_value=10.0,
            value=bond_sector_active_df.at['Active Weight (%)', sector],
            step=1.0
        )
    # Assert that the sum of active weights is 0
    if bond_sector_active_df.sum(axis=1).values[0] != 0:
        st.error("The sum of bond sector active weights must equal 0. Please adjust the weights.")
    else:
        st.success("The sum of bond sector active weights is valid.")
    # Convert the active weights to a dictionary
    bond_sector_active = bond_sector_active_df.iloc[0].to_dict()

# Compute Tactical allocations for stocks size and style using stocks_size_style and stock_style_active
tactical_stocks_size_style = {
    'Large Cap Growth': stocks_size_style['Large Cap Growth'] + stock_style_active['Large Cap Growth'],
    'Large Cap Value': stocks_size_style['Large Cap Value'] + stock_style_active['Large Cap Value'],
    'Small Growth': stocks_size_style['Small Growth'] + stock_style_active['Small Growth'],
    'Small Value': stocks_size_style['Small Value'] + stock_style_active['Small Value'],
    'International: Developed': stocks_size_style['International: Developed'] + stock_style_active['International: Developed'],
    'International: Emerging': stocks_size_style['International: Emerging'] + stock_style_active['International: Emerging']
}
# Compute Tactical allocations for bonds sector using bonds_sector and bond_sector_active
tactical_bonds_sector = {
    'Tsys, CDs & GSEs': bonds_sector['Tsys, CDs & GSEs'] + bond_sector_active['Tsys, CDs & GSEs'],
    'Mortgage Backed': bonds_sector['Mortgage Backed'] + bond_sector_active['Mortgage Backed'],
    'IG Corp & Preferred': bonds_sector['IG Corp & Preferred'] + bond_sector_active['IG Corp & Preferred'],
    'High Yield': bonds_sector['High Yield'] + bond_sector_active['High Yield'],
    'International': bonds_sector['International'] + bond_sector_active['International']
}

# Create dataframe showing stocks styles as rows and strategic and Tactical as columns in that very order in left half and bond sectors in right half
stocks_size_style_df = pd.DataFrame(
    {
        'Strategic': stocks_size_style,
        'Tactical': tactical_stocks_size_style
    },
    index=stocks_size_style.keys()
)
bonds_sector_df = pd.DataFrame(
    {
        'Strategic': bonds_sector,
        'Tactical': tactical_bonds_sector
    },
    index=bonds_sector.keys()
)
col1, col2 = st.columns(2)
with col1:
    st.subheader("Stocks size and style allocations")
    st.dataframe(stocks_size_style_df, use_container_width=True)
with col2:
    st.subheader("Bonds sector allocations")
    st.dataframe(bonds_sector_df, use_container_width=True)

# Create an empty dataframe to show total allocations at level 1 (Stocks, Bonds, Cash) and level 2 (Stocks size and style, Bonds sector)
# Create index by combining index of level_1_allocation_df interspersed with index of dataframes stocks_size_style_df and bonds_sector_df
idx = ['Stocks'] + stocks_size_style_df.index.to_list() + ['Bonds'] + bonds_sector_df.index.to_list() + ['Cash']
cols = level_1_allocation_df.columns
df_total_allocations = pd.DataFrame(index=idx, columns=cols)
for lvl1_asset_class in strategic_allocations.keys():
    df_total_allocations.loc[lvl1_asset_class] = level_1_allocation_df.loc[lvl1_asset_class]
for lvl2_asset_class in stocks_size_style_df.index:
    for typ in ['Strategic', 'Tactical']:
        df_total_allocations.loc[lvl2_asset_class, pd.IndexSlice[:, typ]] = stocks_size_style_df.loc[lvl2_asset_class, typ] * df_total_allocations.loc['Stocks', pd.IndexSlice[:, typ]] / 100
for lvl2_asset_class in bonds_sector_df.index:
    for typ in ['Strategic', 'Tactical']:
        df_total_allocations.loc[lvl2_asset_class, pd.IndexSlice[:, typ]] = bonds_sector_df.loc[lvl2_asset_class, typ] * df_total_allocations.loc['Bonds', pd.IndexSlice[:, typ]] / 100

st.subheader("Total allocations")
st.dataframe(
    df_total_allocations.style
    .format(precision=1)
    .applymap(lambda _: 'font-weight: bold; background-color: #00008B; color: white;', subset=pd.IndexSlice[['Stocks', 'Bonds', 'Cash'], :]),
    use_container_width=True
)