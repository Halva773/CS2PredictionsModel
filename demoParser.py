from demoparser2 import DemoParser
import pandas as pd


class GameStat:
    def __init__(self, href):
        self.result_df = None
        self.parser = DemoParser(href)

        player_stats = ["team_name", 'damage_total', 'utility_damage_total', 'kills_total', 'deaths_total',
                        'assists_total', '3k_rounds_total', '4k_rounds_total', 'ace_rounds_total']
        self.player_death_info = self.parser.parse_event("player_death",
                                                         player=player_stats,
                                                         other=["total_rounds_played", "is_warmup_period"])
        self.__cnt_rounds = self.cnt_rounds()
        # self.player_death_info = self.parser.parse_event("player_death", other=["total_rounds_played"])

    def complain_data(self):
        self.result_df = pd.concat([self.base_stat(), self.total_damage(), self.utility_damage(), self.sniper_kilss()], axis=1)
        # self.result_df.columns = ['total_assits', 'total_deaths', 'total_kills', 'total_damage', 'utility_damage', '3_kills', '4_kills', '5_kills', 'AWP_kills']

        self.result_df['rounds_played'] = self.__cnt_rounds
        self.result_df['start_side'] = 'T'
        for name, side in self.ct_started().items():
            self.result_df.loc[name, 'start_side'] = side

        self.result_df[['hard_clutches', 'light_clutches', 'team_clutches']] = 0

        get_hard_clutches = self.hard_clutches()
        for name, cnt in get_hard_clutches.items():
            self.result_df.loc[name, 'hard_clutches'] = cnt

        get_light_clutches = self.light_clutches()
        for name, cnt in get_light_clutches.items():
            self.result_df.loc[name, 'light_clutches'] = cnt

        get_other_clutches = self.other_clutches()
        for side, cnt in get_other_clutches.items():
            self.result_df.loc[self.result_df['start_side'] == side, 'team_clutches'] = cnt

        single_entries, double_entries = self.count_entry()
        self.result_df.loc[self.result_df.start_side == 'CT', '5v4_situations'] = single_entries['CT start team'][0]
        self.result_df.loc[self.result_df.start_side == 'CT', '5v4_wins'] = single_entries['CT start team'][1]
        self.result_df.loc[self.result_df.start_side == 'CT', '4v5_situations'] = single_entries['T start team'][0]
        self.result_df.loc[self.result_df.start_side == 'CT', '4v5_wins'] = single_entries['T start team'][0] - \
                                                                            single_entries['T start team'][1]
        self.result_df.loc[self.result_df.start_side == 'T', '5v4_situations'] = single_entries['T start team'][0]
        self.result_df.loc[self.result_df.start_side == 'T', '5v4_wins'] = single_entries['T start team'][1]
        self.result_df.loc[self.result_df.start_side == 'T', '4v5_situations'] = single_entries['CT start team'][0]
        self.result_df.loc[self.result_df.start_side == 'T', '4v5_wins'] = single_entries['CT start team'][0] - \
                                                                           single_entries['CT start team'][1]
        return self.result_df

    def base_stat(self):
        max_tick = self.parser.parse_event("round_end")["tick"].max()
        wanted_fields = ["kills_total", "deaths_total", "headshot_kills_total", "ace_rounds_total", "4k_rounds_total",
                         "3k_rounds_total"]
        df = self.parser.parse_ticks(wanted_fields, ticks=[max_tick]).groupby('name').max()
        columns = ['kills_total', 'deaths_total', 'headshot_kills_total', 'ace_rounds_total', '4k_rounds_total',
                   '3k_rounds_total']
        return df[columns]



    def cnt_rounds(self):
        return self.player_death_info.total_rounds_played.max()

    def find_if_yVx(self, round_idx, round_ends, df, X, y):
        for _, death in self.player_death_info.iterrows():
            if death["total_rounds_played"] == round_idx:
                subdf = df[df["tick"] == death["tick"]]
                ct_alive = subdf[(subdf["team_name"] == "CT") & (subdf["is_alive"] == True)]
                t_alive = subdf[(subdf["team_name"] == "TERRORIST") & (subdf["is_alive"] == True)]
                if len(ct_alive) == y and len(t_alive) == X and round_ends.iloc[round_idx]["winner"] == 'CT':
                    if y == 1:
                        return ct_alive["name"].iloc[0]
                    else:
                        return 'CT'
                if len(t_alive) == y and len(ct_alive) == X and round_ends.iloc[round_idx]["winner"] == 'T':
                    if y == 1:
                        return t_alive["name"].iloc[0]
                    else:
                        return 'T'

    def hard_clutches(self):
        round_ends = self.parser.parse_event("round_end")
        df = self.parser.parse_ticks(["is_alive", "team_name", "team_rounds_total"],
                                     ticks=self.player_death_info["tick"].to_list())
        max_round = self.player_death_info["total_rounds_played"].max() + 1
        clutches_list = {}
        for enemies in range(3, 6):
            for round_idx in range(0, max_round):
                clutcher_steamid = self.find_if_yVx(round_idx, round_ends, df, enemies, 1)
                if clutcher_steamid != None:
                    clutches_list[clutcher_steamid] = clutches_list.get(clutcher_steamid, 0) + 1
        return clutches_list

    def light_clutches(self):
        round_ends = self.parser.parse_event("round_end")
        df = self.parser.parse_ticks(["is_alive", "team_name", "team_rounds_total"],
                                     ticks=self.player_death_info["tick"].to_list())
        max_round = self.player_death_info["total_rounds_played"].max() + 1
        clutches_list = {}
        for enemies in range(1, 3):
            for round_idx in range(0, max_round):
                clutcher_steamid = self.find_if_yVx(round_idx, round_ends, df, enemies, 1)
                if clutcher_steamid != None:
                    clutches_list[clutcher_steamid] = clutches_list.get(clutcher_steamid, 0) + 1
        return clutches_list

    def other_clutches(self):
        round_ends = self.parser.parse_event("round_end")
        df = self.parser.parse_ticks(["is_alive", "team_name", "team_rounds_total"],
                                     ticks=self.player_death_info["tick"].to_list())
        max_round = self.player_death_info["total_rounds_played"].max() + 1
        clutches_list = {}
        for mates in range(2, 4):
            for enemies in range(mates + 2, 6):
                for round_idx in range(0, max_round):
                    clutcher_steamid = self.find_if_yVx(round_idx, round_ends, df, enemies, mates)
                    if clutcher_steamid != None:
                        clutches_list[clutcher_steamid] = clutches_list.get(clutcher_steamid, 0) + 1
        return clutches_list

    def count_entry(self):
        round_ends = self.parser.parse_event("round_end")
        df = self.parser.parse_ticks(["is_alive", "team_name", "team_rounds_total"],
                                     ticks=self.player_death_info["tick"].to_list())
        max_round = self.player_death_info["total_rounds_played"].max() + 1
        single_entry = {'CT start team': [0, 0],
                        'T start team': [0, 0]}
        double_entry = {'CT start team': [0, 0],
                        'T start team': [0, 0]}
        for round_idx in range(0, max_round):
            for _, death in self.player_death_info.iterrows():
                if death["total_rounds_played"] == round_idx:
                    subdf = df[df["tick"] == death["tick"]]
                    ct_alive = subdf[(subdf["team_name"] == "CT") & (subdf["is_alive"] == True)]
                    t_alive = subdf[(subdf["team_name"] == "TERRORIST") & (subdf["is_alive"] == True)]
                    if len(ct_alive) == 5 and len(t_alive) == 4:
                        single_entry['CT start team' if round_idx < 12 else 'T start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'CT':
                            single_entry['CT start team' if round_idx < 12 else 'T start team'][1] += 1
                        continue
                    if len(ct_alive) == 4 and len(t_alive) == 5:
                        single_entry['T start team' if round_idx < 12 else 'CT start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'T':
                            single_entry['T start team' if round_idx < 12 else 'CT start team'][1] += 1
                        continue
                    if len(ct_alive) == 5 and len(t_alive) == 3:
                        double_entry['CT start team' if round_idx < 12 else 'T start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'CT':
                            double_entry['CT start team' if round_idx < 12 else 'T start team'][1] += 1
                        continue
                    if len(ct_alive) == 3 and len(t_alive) == 5:
                        double_entry['T start team' if round_idx < 12 else 'CT start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'T':
                            double_entry['T start team' if round_idx < 12 else 'CT start team'][1] += 1
                        continue
        return single_entry, double_entry

    def total_damage(self):
        return self.player_death_info[['user_name', 'user_damage_total']].groupby('user_name').max()

    def utility_damage(self):
        return self.player_death_info[['user_name', 'user_utility_damage_total']].groupby('user_name').max()

    def ct_started(self):
        player_death_info = self.player_death_info
        return player_death_info[(player_death_info['user_team_name'] == 'CT') & (
                player_death_info['total_rounds_played'] == 0)].groupby('user_name').max()['user_team_name']


    def sniper_kilss(self):
        columns_list = ['attacker_name', 'weapon']
        return self.player_death_info[self.player_death_info['weapon'] == 'awp'][columns_list].groupby('attacker_name').count().rename(columns={'weapon': 'AWP_kills'})


def main():
    # https://www.hltv.org/matches/2373289/g2-vs-natus-vincere-esports-world-cup-2024
    src = "demos/mouz-nxt-vs-rhyno-m1-ancient.dem"
    stat = GameStat(src)
    df = stat.complain_data()
    print(df.columns)
    need_columns = ['start_side', 'utility_damage', '4_kills']
    print(df)
    return stat


if __name__ == '__main__':
    stat = main()
    columns = ['start_side', '5v4_situations', '5v4_wins', '4v5_situations', '4v5_wins']
    print(stat.result_df[columns])