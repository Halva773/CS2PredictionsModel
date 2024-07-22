from demoparser2 import DemoParser


class GameStat:
    def __init__(self, href):
        self.parser = DemoParser(href)
        self.player_death_info = self.parser.parse_event("player_death", player=["team_name"],
                                                         other=["total_rounds_played", "is_warmup_period"])
        self.__cnt_rounds = self.cnt_rounds()

    def kpr(self):
        # filter out team-kills and warmup
        self.player_death_info = self.player_death_info[
            self.player_death_info["attacker_team_name"] != self.player_death_info["user_team_name"]]
        self.player_death_info = self.player_death_info[self.player_death_info["is_warmup_period"] == False]
        # group-by like in sql
        self.player_death_info = self.player_death_info.groupby(
            ["total_rounds_played", "attacker_name"]).size().to_frame(name='total_kills').reset_index()
        return self.player_death_info.groupby(
            'attacker_name').sum().total_kills/self.__cnt_rounds

    def cnt_rounds(self):
        return self.player_death_info.total_rounds_played.max()

    def find_if_1vx(self, deaths, round_idx, round_ends, df, X):
        for _, death in deaths.iterrows():
            if death["total_rounds_played"] == round_idx:

                subdf = df[df["tick"] == death["tick"]]
                ct_alive = subdf[(subdf["team_name"] == "CT") & (subdf["is_alive"] == True)]
                t_alive = subdf[(subdf["team_name"] == "TERRORIST") & (subdf["is_alive"] == True)]
                if len(ct_alive) == 1 and len(t_alive) == X and round_ends.iloc[round_idx]["winner"] == 'CT':
                    return ct_alive["name"].iloc[0]
                if len(t_alive) == 1 and len(ct_alive) == X and round_ends.iloc[round_idx]["winner"] == 'T':
                    return t_alive["name"].iloc[0]

    def hard_clutches(self):
        deaths = self.parser.parse_event("player_death", other=["total_rounds_played"])
        round_ends = self.parser.parse_event("round_end")
        df = self.parser.parse_ticks(["is_alive", "team_name", "team_rounds_total"], ticks=deaths["tick"].to_list())
        max_round = deaths["total_rounds_played"].max() + 1
        clutches_list = set()
        for enemies in range(3, 6):
            for round_idx in range(0, max_round):
                clutcher_steamid = self.find_if_1vx(deaths, round_idx, round_ends, df, enemies)
                if clutcher_steamid != None:
                    clutches_list.add(round_idx)
        return len(clutches_list)

    def light_clutches(self):
        deaths = self.parser.parse_event("player_death", other=["total_rounds_played"])
        round_ends = self.parser.parse_event("round_end")
        df = self.parser.parse_ticks(["is_alive", "team_name", "team_rounds_total"], ticks=deaths["tick"].to_list())
        max_round = deaths["total_rounds_played"].max() + 1
        clutches_list = set()
        for enemies in range(1, 3):
            for round_idx in range(0, max_round):
                clutcher_steamid = self.find_if_1vx(deaths, round_idx, round_ends, df, enemies)
                if clutcher_steamid != None:
                    clutches_list.add(round_idx)
        return len(clutches_list)


if __name__ == '__main__':
    src = "demos/g2-vs-natus-vincere-m1-ancient.dem"
    stat = GameStat(src)
    print(stat.hard_clutches())
    print(stat.light_clutches())