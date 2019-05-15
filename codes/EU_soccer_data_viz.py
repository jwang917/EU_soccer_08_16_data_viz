# support functions.
import sqlite3
import pandas as pd
import seaborn as sns
import itertools
import matplotlib.pyplot as plt
import os

import plotly.graph_objs as go
import sys
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot


# define the fields to be used.
tech_att_name = ["ball_control","dribbling","short_passing","vision","crossing","long_passing","curve"]
physical_att_name = ['acceleration',"sprint_speed","agility","reactions","jumping","stamina","strength","balance"]
finishing_att_name = ["volleys","heading_accuracy","finishing","free_kick_accuracy","long_shots","shot_power","penalties"]
def_att_name = ["aggression","interceptions","positioning","marking","standing_tackle","sliding_tackle"]
gk_att_name = ['gk_diving', 'gk_handling', 'gk_kicking','gk_positioning', 'gk_reflexes']
general_att_name =["overall_rating","potential"]

FOCUS_DICT = {"technical":tech_att_name, "physical":physical_att_name, "finishing":finishing_att_name, "defensive":def_att_name,
            "goal_keeping":gk_att_name,"general":general_att_name}

query = "select * from League;"
league_df = _get_table(query, conn)
league_name = league_df.name

# helper function to set up connection to database.
def _conn_db(path):
    database = os.path.join(path, 'database.sqlite')
    conn = sqlite3.connect(database)
    return conn


# helper function to get the data.
def _get_table(query,conn):
    df = pd.read_sql(query,conn)
    return df


# function to make goal difference on each season.
def _goal_dif_season(season, match_df, period):
    # get data for that season.
    goal_dif = match_df[match_df.season==season][["home_team_goal","away_team_goal","date"]]
    # make new columns on date.
    goal_dif["home_goal_dif"] = goal_dif.home_team_goal - goal_dif.away_team_goal
    goal_dif["my_date"] = pd.to_datetime(goal_dif.date)
    if period == "dow":
        goal_dif["match_dow"] = goal_dif.my_date.dt.day_name()
        # get the goal dif on dow.
        goal_dif_period = goal_dif.groupby(by="match_dow").mean()[["home_goal_dif","home_team_goal","away_team_goal"]]
    elif period == 'month':
        goal_dif["match_month"] = goal_dif.my_date.dt.month
        goal_dif_period = goal_dif.groupby(by="match_month").mean()[["home_goal_dif","home_team_goal","away_team_goal"]]
    goal_dif_period.reset_index(inplace=True)
    return goal_dif_period



# the drawing function to make goal difference on each season.
def _draw_goal_dif(goal_dif, season, period):
    # get index
    if period == "dow":
        colors = ["#66CDAA", "#E3CF57", "#1C86EE"]
        order = ["Monday", "Tuesday", "Wednesday",
                 "Thursday", "Friday", "Saturday", "Sunday"]
        ind1 = [list(goal_dif.match_dow).index(i) for i in order]
    elif period == "month":
        # get colors list. [lightblue1,lightcyan2,lightgrey,chartreuse1,chartreuse3,
        # darkgreen,cornflowerblue,aquamarine3, dodgerblue2, banana,darkorange,darkorange3]
        colors = ["#BFEFFF", "#D1EEEE", "#D3D3D3", "#6495ED", "#66CD00",
                  "#006400", "#66CDAA", "#1C86EE", "#E3CF57", "#FF8C00", "#CD6600"]
        order = list(range(1, 6)) + list(range(7,13))
        ind1 = [list(goal_dif.match_month).index(i) for i in order]
    line_colours = ["#DC143C","#1C86EE","#006400"]
    # build traces
    data = []
    cols = ["home_goal_dif", "home_team_goal", "away_team_goal"]
    names = ["Home Goals - Away Goals", "Home Goals", "Away Goals"]
    for ind, col_name in enumerate(cols):
        trace = go.Scatter(
            x=order,
            y=goal_dif[col_name][ind1],
            name=names[ind],
            text=["Mean goal difference:"+str(round(i,2))
                  for i in goal_dif[col_name]],
            marker=dict(
                color=line_colours[ind],
                line=dict(
                    color=line_colours[ind],
                    width=1.5,
                )
            ),
            opacity=1
        )
        data.append(trace)
    layout = go.Layout(
        title="The average goal difference in season %s per %s." % (
            season, period),
        xaxis=dict(
            title=period
        ),
        yaxis=dict(
            title='Goal Differences'
        ),
        bargap=0.2,
        bargroupgap=0.1,
        paper_bgcolor='rgb(243, 243, 243)',
        plot_bgcolor='rgb(243, 243, 243)'
    )
    fig1 = go.Figure(data=data, layout=layout)
    return fig1


def _bin_cont(df,name,method):
    """
    To categorize continuous data by different method defind.
    param:
        df the data source
        name the column's name.
        method: the intended usage, could be boxplot, outliers,TBE(to be extended.)
    return:
        binned_df
    """
    if method == "boxplot":
        IQR = (df[name].quantile(0.75) - df[name].quantile(0.25));
        Q1 = df[name].quantile(0.25)
        Q3 = df[name].quantile(0.75)
        median = df[name].quantile(0.5)
        upp = Q3 + 1.5*IQR
        low = Q1 - 1.5*IQR
        mi = min(df[name])
        ma = max(df[name])
        binned_df = pd.cut(df[name],[mi,low,median,upp,ma],right =True,labels=["Amateur","Below_Average","Above_Average","Very_Promising"])
    df[name+"_category"] = binned_df
    return df


# a function to get the player's meta attributes's distribution info.
def _boxplot_player(df, col_names,method):
    """
    The function is to show the Grouped Horizontal box plot for players in different groups of columns.
    param:
        col_names is the column name that we want to investigate.
    return: 
        a fig object.
    """
    # define color maps
    colors = ["#6495ED", 
                  "#006400", "#66CDAA", "#1C86EE", "#E3CF57", "#FF8C00", "#CD6600"]
    # categorize data based on standard deviation and boxplot's separation.
    for name in col_names:
        df = _bin_cont(df, name,method)
    # make trace 
    data = []
    for ind,name in enumerate(col_names):
        trace1 = go.Box(
                x= df[name],
                y= df[name+"_category"],
                name=name,
                marker=dict(color=colors[ind+3]),
                boxmean=False,
                orientation = 'h'
            )
        data.append(trace1)
    # defin proper name
    name = ", ".join(col_names[:-1])
    name += " & " + col_names[-1]
    layout = go.Layout(
        title="The distribution of player's %s" % name,
        xaxis=dict(
            title="Player Value",
            zeroline=  False
        ),
        bargap=0.2,
        bargroupgap=0.1,
        paper_bgcolor='rgb(243, 243, 243)',
        plot_bgcolor='rgb(243, 243, 243)',
        yaxis = dict(automargin=True),
        boxmode = "group"
        
    )
    fig1 = go.Figure(data=data, layout=layout)
    # return object.
    return fig1


def _make_history_player_att(focus):
    """
    This function is to plot player's attributes overall change.
    param:
        focus: the category we want to see, it can be technical,physical, finishing, defensive,goal_keeping or general.
    return: 
        fig object to plot.
    """
    # get attributes name
    att_ls = FOCUS_DICT[focus]
    # get data, we need deduplicated aggregated player's data.
    df = _get_clean_paly_att_data(att_ls)
    # build traces.
    agg_df = df.groupby(by="birth_year").mean()[att_ls]
    data = []
    for ind,i in enumerate(agg_df):
        trace = go.Bar(
        x=agg_df.index.values,
        y=agg_df[i].values,
        name=i,
        marker=dict( color= COLORS[ind])
        )
        data.append(trace)
    # add layout
    layout = go.Layout(
    title="Player's {} abilities change over time.".format(focus),
    xaxis=dict(
        title='Birth Year',
        titlefont=dict(
            family='Old Standard TT, serif',
            size=18,
            color='Brown'
        ),
        showticklabels=True,
        tickangle=30,
        tickfont=dict(
            family='Old Standard TT, serif',
            size=14,
            color='black'
        )
    ),
    yaxis=dict(
        range=[50, 75],
        title='Score Value',
        titlefont=dict(
            family='Old Standard TT, serif',
            size=18,
            color='black'
        ),
        tickfont=dict(
            size=14,
            color='rgb(107, 107, 107)'
        )
    ),
    legend=dict(
        bgcolor='rgba(255, 255, 255, 0)',
        bordercolor='rgba(255, 255, 255, 0)'
    ),
    barmode='group',
    bargap=0.15,
    bargroupgap=0.1
)

    fig = go.Figure(data=data, layout=layout)
    # return fig object.
    return fig


def _get_clean_paly_att_data(att_ls):
    """
    Get the joined table of player's attributes and play information. And aggregated on birth year.
    param:
        att_ls: the attribute names list.
    """
    command = [ "round(avg("+i+")) as "+i for i in att_ls]
    de_dup_paly_att_query = "select player_api_id, {} from Player_Attributes \
                            group by player_api_id".format(", ".join(command))
    query = "select r.player_name, r.player_api_id, strftime('%Y',r.birthday) as birth_year ,\
        l.{} from ({}) as l left join Player as \
        r on r.player_api_id = l.player_api_id;".format(", l.".join(att_ls), de_dup_paly_att_query) 
    new_player_att_df = _get_table(query, conn)
    return new_player_att_df


def _get_league_score_on_year(league_name, season):
    """Get the specified leagues's total games on certain season.""" 
    # get table with team name along with home goal and away goal.
    query = "select r3.name as League_name, r.team_long_name as home_team_name1, \
        r.team_short_name as home_team_name2,r2.team_long_name as away_team_name1, r2.team_short_name as \
        away_team_name2,l.season,l.home_team_goal,l.away_team_goal from Match as l left join Team as r \
        on l.home_team_api_id = r.team_api_id \
        left join Team as r2 \
        on l.away_team_api_id=r2.team_api_id\
        left join League as r3\
        on l.league_id = r3.id;"
    df = _get_table(query, conn)
    # get all matches in one season for one league.
    res_df = df[(df.League_name == league_name) & (df.season == season)]
    # get all goals scored in home and away team.
    all_goals = [sum(res_df.home_team_goal),sum(res_df.away_team_goal)]
    # get individual teams goal
    teams_goals_df = res_df.groupby(by = "home_team_name1").sum()[["home_team_goal","away_team_goal"]]
    teams_goals_df["tot_goals"] = teams_goals_df.home_team_goal + teams_goals_df.away_team_goal
    top_4_home_teams = teams_goals_df.sort_values(by="tot_goals",ascending=False).head(4)
    return top_4_home_teams


def _plot_top_attact_team(league_name):
    """
    Get the plot for each leagues' top 4 attacking teams goals stat over the years.
    param:
        league_name: the name of the league.
    return:
        fig: object to draw.
    """
    data = []
    # build up traces.
    for season in season_ls:
        # get the data
        df = _get_league_score_on_year(league_name, season)
        trace = go.Bar(
                x=df.index.values,
                y=(df.home_team_goal + df.away_team_goal).values,
                name=season
                )
        data.append(trace)
        
        layout = go.Layout(
        barmode='stack',
        title="Top 4 Attacking Teams On Each Season in {}".format(league_name),
        xaxis=dict(
            title='Team Name',
            titlefont=dict(
                family='Old Standard TT, serif',
                size=14,
                color='black'
            )
        ),
        yaxis=dict(
            title='Number of Goals',
            titlefont=dict(
                family='Old Standard TT, serif',
                size=18,
                color='black'
            )
        )
    )

    fig = go.Figure(data=data, layout=layout)
    return fig



# get the 
query = "select distinct l.team_long_name,l.team_fifa_api_id, l.team_short_name,r.country_id, \
        r2.name from Team as l left join Match as r on l.team_api_id = r.home_team_api_id\
        left join League as r2 on r2.country_id = r.country_id;"
new_team_df = _get_table(query, conn)