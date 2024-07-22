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


if __name__ == '__main__':
    src = "demos/g2-vs-natus-vincere-m1-ancient.dem"
    stat = GameStat(src)
    print(stat.kpr())