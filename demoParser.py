from demoparser2 import DemoParser
import pandas as pd


class GameStat:
    def __init__(self, href):
        self.parser = DemoParser(href)
        self.player_death_info = self.parser.parse_event("player_death",
                                                         player=["team_name", 'damage_total', 'utility_damage_total'],
                                                         other=["total_rounds_played", "is_warmup_period"])
        self.__cnt_rounds = self.cnt_rounds()
        # self.player_death_info = self.parser.parse_event("player_death", other=["total_rounds_played"])

    def complain_data(self):
        self.result_df = pd.concat([self.kpr(), self.adr(), self.utility_damage()], axis=1)
        self.result_df.columns = ['krp', 'adr', 'utility damage']

        self.result_df['start side'] = 'T'
        for name, side in self.ct_started().items():
            self.result_df.loc[name, 'start side'] = side



        self.result_df[['hard clutches', 'light clutches', 'team clutches']] = 0

        get_hard_clutches = self.hard_clutches()
        for name, cnt in get_hard_clutches.items():
            self.result_df.loc[name, 'hard clutches'] = cnt

        get_light_clutches = self.light_clutches()
        for name, cnt in get_light_clutches.items():
            self.result_df.loc[name, 'light clutches'] = cnt

        get_other_clutches = self.other_clutches()
        for side, cnt in get_other_clutches.items():
            self.result_df.loc[self.result_df['start side'] == side, 'team clutches'] = cnt
        print(self.result_df)

    def kpr(self):
        player_death_info = self.player_death_info
        # filter out team-kills and warmup
        player_death_info = player_death_info[
            player_death_info["attacker_team_name"] != player_death_info["user_team_name"]]
        player_death_info = player_death_info[player_death_info["is_warmup_period"] == False]
        # group-by like in sql
        player_death_info = player_death_info.groupby(
            ["total_rounds_played", "attacker_name"]).size().to_frame(name='total_kills').reset_index()
        return player_death_info.groupby(
            'attacker_name').sum().total_kills / self.__cnt_rounds

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
            for enemies in range(mates + 1, 6):
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
                        single_entry['T start team' if round_idx < 12 else 'CT start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'T':
                            single_entry['T start team' if round_idx < 12 else 'CT start team'][1] += 1
                        continue
                    if len(ct_alive) == 4 and len(t_alive) == 5:
                        single_entry['CT start team' if round_idx < 12 else 'T start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'CT':
                            single_entry['CT start team' if round_idx < 12 else 'T start team'][1] += 1
                        continue
                    if len(ct_alive) == 5 and len(t_alive) == 3:
                        double_entry['T start team' if round_idx < 12 else 'CT start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'T':
                            single_entry['T start team' if round_idx < 12 else 'CT start team'][1] += 1
                        continue
                    if len(ct_alive) == 3 and len(t_alive) == 5:
                        double_entry['CT start team' if round_idx < 12 else 'T start team'][0] += 1
                        if round_ends.iloc[round_idx]["winner"] == 'CT':
                            single_entry['CT start team' if round_idx < 12 else 'T start team'][1] += 1
                        continue
        return single_entry, double_entry

    def adr(self):
        return self.player_death_info[['user_name', 'user_damage_total']].groupby('user_name').max() / self.__cnt_rounds

    def utility_damage(self):
        return self.player_death_info[['user_name', 'user_utility_damage_total']].groupby('user_name').max()

    def ct_started(self):
        player_death_info = self.player_death_info
        return player_death_info[(player_death_info['ct_team_name'] == 'CT') & (
                    player_death_info['total_rounds_played'] == 0)].groupby('user_name').max()['user_team_name']

    def introducing(self):
        print(f'KRP: ', self.kpr())
        print(f'ADR: ', self.adr())
        print(f'Entry kills ([5v4 cnt, 4v5 won], [5v3 cnt, 3v5 won]): ', self.count_entry())
        print(f'Count of clutches where was 1v3+', self.hard_clutches())
        print(f'Count of clutches where was 1v(1/2)', self.light_clutches())
        print(f'Other clutches (2v3+, 3v4+)', self.other_clutches())


def main():
    src = "demos/g2-vs-natus-vincere-m1-ancient.dem"
    stat = GameStat(src)
    stat.complain_data()


if __name__ == '__main__':
    main()
