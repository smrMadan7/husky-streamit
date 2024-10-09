import pandas as pd
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components


@st.cache_data
def load_data(file):
    """Loads the CSV file into a DataFrame."""
    return pd.read_csv(file)


def display_filters(df):
    """Displays the network filters and applies the selected filter."""
    avg_connections = df['ConnectionCount'].mean()
    max_connections = df['ConnectionCount'].max()
    min_connections = df['ConnectionCount'].min()

    filter_option = st.selectbox(
        "Filter by connection count",
        options=["None", "Above Average", "Below Average", "Minimum", "Maximum"]
    )

    if filter_option == "Above Average":
        filtered_df = df[df['ConnectionCount'] > avg_connections].reset_index(drop=True)
        return filtered_df

    elif filter_option == "Below Average":
        filtered_df = df[df['ConnectionCount'] < avg_connections].reset_index(drop=True)
        return filtered_df

    elif filter_option == "Minimum":
        filtered_df = df[df['ConnectionCount'] == min_connections].reset_index(drop=True)
        return filtered_df

    elif filter_option == "Maximum":
        filtered_df = df[df['ConnectionCount'] == max_connections].reset_index(drop=True)
        return filtered_df

    return df  # Return the original dataframe if no filter is applied


def visualize_network(filtered_df):
    """Creates and displays the network graph using the filtered data."""
    net = Network(height='900px', width='100%', notebook=True)

    for _, row in filtered_df.iterrows():
        source = row['Member']
        target = row['NetworkConnections']
        relationship = row.get('Relationship', 'Twitter')

        net.add_node(source, label=source, title=f"Member: {source}", color='green', borderColor='green', size=10)
        net.add_node(target, label=target, title=f"Connection {target}", color='blue', borderColor='green', size=10)

        net.add_edge(source, target, title=f"Relationship: {relationship}", color='purple')

    options = """
    {
        "nodes": {
            "font": {
                "size": 10
            },
            "shape": "dot"
        },
        "edges": {
            "smooth": {
                "type": "continuous"
            }
        },
        "physics": {
            "enabled": true
        },
        "background": {
            "color": "#ccffcc"
        }
    }
    """
    net.set_options(options)
    net.show('network_graph.html')
    HtmlFile = open('network_graph.html', 'r', encoding='utf-8')
    source_code = HtmlFile.read()
    components.html(source_code, height=900, width=1100, scrolling=True)


def main():
    """Main function to run the Streamlit app."""
    st.title("PL Network Visualization")
    st.sidebar.title("Upload Network Data")
    uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        df = load_data(uploaded_file)
        df['ConnectionCount'] = df['NetworkConnections'].apply(lambda x: len(x.split(', ')))

        unique_members = pd.concat([df['Member'], df['NetworkConnections']]).unique()
        selected_member = st.selectbox("Select a member to filter connections", options=['All'] + list(unique_members))

        if selected_member != 'All':
            filtered_df = df[(df['Member'] == selected_member) | (df['NetworkConnections'] == selected_member)]
            visualize_network(filtered_df)
        else:
            filtered_df = display_filters(df)
            if not filtered_df.empty:
                st.dataframe(filtered_df, height=300)  # Display DataFrame with a scrollable view
                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(label="Download Filtered Data", data=csv_data, file_name='filtered_network_data.csv', mime='text/csv')
                visualize_network(filtered_df)
            else:
                st.warning("No connections found with the selected filters.")


if __name__ == "__main__":
    main()
