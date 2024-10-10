import pandas as pd
import streamlit as st
from pyvis.network import Network
import streamlit.components.v1 as components
import plotly.express as px


@st.cache_data
def load_data(file):
    """Loads the CSV file into a DataFrame."""
    return pd.read_csv(file)


def calculate_network_strength(df, total_members=2000):
    """Calculates the network strength as the percentage of unique connected members."""
    unique_members = set(df['Member']).union(set(', '.join(df['NetworkConnections']).split(', ')))
    unique_count = len(unique_members)
    network_strength = (unique_count / total_members) * 100
    return unique_count, network_strength


def calculate_member_statistics(df):
    """Calculates statistics for each member."""
    member_stats = df.groupby('Member')['NetworkConnections'].apply(
        lambda x: ', '.join(x) if x.size > 0 else '').reset_index()
    member_stats['ConnectionCount'] = member_stats['NetworkConnections'].str.split(', ').apply(len)
    return member_stats


def calculate_team_statistics(df):
    """Calculates interaction counts for each team and their statistics."""
    df['Network_Connections_Teams'] = df['Network_Connections_Teams'].fillna('').astype(str)
    team_interaction_counts = df.groupby('Member_Teams')['Network_Connections_Teams'].apply(
        lambda x: ', '.join(x) if x.size > 0 else ''
    ).reset_index()
    team_interaction_counts['Network_Connections_Teams'] = team_interaction_counts[
        'Network_Connections_Teams'].str.split(', ')
    exploded_counts = team_interaction_counts.explode('Network_Connections_Teams')
    team_stats = exploded_counts['Network_Connections_Teams'].value_counts().reset_index()
    team_stats.columns = ['Team', 'Count']
    return team_stats


def create_bubble_chart(team_stats):
    """Creates a bubble chart for team statistics."""
    # Calculate average counts
    average_count = team_stats['Count'].mean()
    max_count = team_stats['Count'].max()
    min_count = team_stats['Count'].min()

    # Prepare data for bubble chart
    stats_df = pd.DataFrame({
        'Category': ['Above Average', 'Below Average', 'Maximum', 'Minimum'],
        'Count': [
            len(team_stats[team_stats['Count'] > average_count]),
            len(team_stats[team_stats['Count'] < average_count]),
            len(team_stats[team_stats['Count'] == max_count]),
            len(team_stats[team_stats['Count'] == min_count])
        ]
    })

    fig = px.scatter(
        stats_df,
        x='Category',
        y='Count',
        size='Count',
        hover_name='Category',
        title='Team Interaction Statistics',
        labels={'Count': 'Number of Teams', 'Category': 'Interaction Category'},
        size_max=60  # Adjust the maximum size of the bubbles
    )

    st.plotly_chart(fig)

    return stats_df  # Return the stats DataFrame for further processing


def create_stacked_bar_chart(selected_category, team_stats):
    """Creates a stacked bar chart for team statistics based on the selected category."""
    if selected_category == "Above Average":
        filtered_teams = team_stats[team_stats['Count'] > team_stats['Count'].mean()]
    elif selected_category == "Below Average":
        filtered_teams = team_stats[team_stats['Count'] < team_stats['Count'].mean()]
    elif selected_category == "Maximum":
        filtered_teams = team_stats[team_stats['Count'] == team_stats['Count'].max()]
    elif selected_category == "Minimum":
        filtered_teams = team_stats[team_stats['Count'] == team_stats['Count'].min()]

    # Prepare data for stacked bar chart
    fig = px.bar(filtered_teams,
                 x='Team',
                 y='Count',
                 title=f'Teams with {selected_category} Interactions',
                 labels={'Team': 'Team', 'Count': 'Interaction Count'},
                 color='Team',
                 text=None)  # Remove text from the bar chart

    st.plotly_chart(fig)


def display_filters(df):
    """Displays the network filters and applies the selected filter."""
    avg_connections = df['ConnectionCount'].mean()
    max_connections = df['ConnectionCount'].max()
    min_connections = df['ConnectionCount'].min()

    filter_option = st.selectbox(
        "Filter by connection count",
        options=["None", "Above Average", "Below Average", "Minimum", "Maximum"]
    )

    if filter_option == "None":
        filtered_df = df
        return filter_option, filtered_df

    if filter_option == "Above Average":
        filtered_df = df[df['ConnectionCount'] > avg_connections].reset_index(drop=True)
        return filter_option,filtered_df

    elif filter_option == "Below Average":
        filtered_df = df[df['ConnectionCount'] < avg_connections].reset_index(drop=True)
        return filter_option,filtered_df

    elif filter_option == "Minimum":
        filtered_df = df[df['ConnectionCount'] == min_connections].reset_index(drop=True)
        return filter_option,filtered_df

    elif filter_option == "Maximum":
        filtered_df = df[df['ConnectionCount'] == max_connections].reset_index(drop=True)
        return filter_option,filtered_df

    return df  # Return the original dataframe if no filter is applied


def visualize_network(filtered_df):
    """Creates and displays the network graph using the filtered data."""
    net = Network(height='900px', width='100%', notebook=True)

    for _, row in filtered_df.iterrows():
        source = row['Member']
        target = row['NetworkConnections']
        if "AreaOfInterest" in filtered_df.columns:
            relationship=row['AreaOfInterest']
        else:
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
        df['ConnectionCount'] = df['NetworkConnections'].apply(lambda x: len(x.split(',')))

        # Calculate unique members and network strength
        unique_count, network_strength = calculate_network_strength(df)

        # Display network strength
        st.metric(label="Member Network Strength", value=f"{network_strength:.2f}%")
        st.progress(network_strength / 100)

        # Team Strength Indicator
        total_teams = 600  # Assuming total teams is 600
        unique_teams_count = df['Member_Teams'].nunique()  # Calculate unique teams for strength
        team_strength_percentage = (unique_teams_count / total_teams) * 100
        st.metric(label="Team Network Strength", value=f"{team_strength_percentage:.2f}%")
        st.progress(team_strength_percentage/100)

        # Dropdown for Members or Teams
        selection_type = st.selectbox("Select:", options=["Member", "Team"])

        if selection_type == "Member":
            # Dropdown for members
            unique_members = df['Member'].unique()
            selected_member = st.selectbox("Select a member:", options=['All'] + list(unique_members))


            if selected_member != 'All':
                filtered_df = df[(df['Member'] == selected_member) | (df['NetworkConnections'] == selected_member)]
                visualize_network(filtered_df)
            else:
                option,filtered_df = display_filters(df)
                if not filtered_df.empty:
                    st.dataframe(filtered_df, height=300)  # Display DataFrame with a scrollable view
                    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                    filename=option+"_network_data.csv"
                    st.download_button(label="Download Filtered Data", data=csv_data,
                                       file_name=filename, mime='text/csv')
                    visualize_network(filtered_df)
                else:
                    st.warning("No connections found with the selected filters.")


        else:  # Team selected
            # Dropdown for teams
            unique_teams = df['Member_Teams'].unique()
            selected_team = st.selectbox("Select a team:", options=['All'] + list(unique_teams))

            # Calculate team statistics and create the bubble chart
            team_stats = calculate_team_statistics(df)
            if selected_team != 'All':
                team_stats = team_stats[team_stats['Team'] == selected_team]

            # Create bubble chart for team statistics
            stats_df = create_bubble_chart(team_stats)

            # Dropdown for stats options
            selected_category = st.selectbox("Select stats category:",
                                             options=["None", "Above Average", "Below Average", "Maximum", "Minimum"])
            if selected_category != "None":
                create_stacked_bar_chart(selected_category, team_stats)


if __name__ == "__main__":
    main()
