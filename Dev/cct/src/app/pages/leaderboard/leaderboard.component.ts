import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import imafiaData from 'public/imafia.json';

interface RawResponse {
  status: number;
  games: Array<{ first_blood: string; players: Record<string, any> }>;
}

interface PlayerStats {
  name: string;
  plus: number;
  minus: number;
  bm: number;
  comp: number;
  wins: number;
  games: number;
  rawNetAdj: number;
  netAdj: number;
  rawTotalPoints: number;
  totalPoints: number;
  firstBloods: number;
  role1Total: number; role1Wins: number;
  role2Total: number; role2Wins: number;
  role3Total: number; role3Wins: number;
  role4Total: number; role4Wins: number;
  place?: number;
}

@Component({
  selector: 'app-leaderboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './leaderboard.component.html',
  styleUrls: ['./leaderboard.component.css']
})
export class LeaderboardComponent implements OnInit {
  leaderboard: PlayerStats[] = [];

  ngOnInit() {
    const { games } = imafiaData as RawResponse;
    const statsMap = new Map<string, PlayerStats>();
    const toNum = (v: unknown) => +(v || 0);

    games.forEach(({ first_blood, players }) => {
      Object.values(players).forEach(({ players_id, name, points_plus, points_minus, points_bm, points_compensation, win, position, roles_id }: any) => {
        const key = players_id;
        if (!statsMap.has(key)) {
          statsMap.set(key, {
            name,
            plus: 0,
            minus: 0,
            bm: 0,
            comp: 0,
            wins: 0,
            games: 0,
            rawNetAdj: 0,
            netAdj: 0,
            rawTotalPoints: 0,
            totalPoints: 0,
            firstBloods: 0,
            role1Total: 0, role1Wins: 0,
            role2Total: 0, role2Wins: 0,
            role3Total: 0, role3Wins: 0,
            role4Total: 0, role4Wins: 0
          });
        }

        const stat = statsMap.get(key)!;
        const won = win === '1';

        stat.plus += toNum(points_plus);
        stat.minus += toNum(points_minus);
        stat.bm += toNum(points_bm);
        stat.comp += toNum(points_compensation);
        stat.wins += won ? 1 : 0;
        stat.games += 1;
        if (position === first_blood) stat.firstBloods++;

        switch (roles_id) {
          case '1': stat.role1Total++; if (won) stat.role1Wins++; break;
          case '2': stat.role2Total++; if (won) stat.role2Wins++; break;
          case '3': stat.role3Total++; if (won) stat.role3Wins++; break;
          case '4': stat.role4Total++; if (won) stat.role4Wins++; break;
        }
      });
    });

    this.leaderboard = Array.from(statsMap.values()).map(stat => {
      const rawNetAdj = stat.plus + stat.minus + stat.bm;
      const netAdj = Math.round(rawNetAdj * 10) / 10;
      const rawTotalPoints = stat.wins + stat.comp + rawNetAdj;
      const totalPoints = Math.round(rawTotalPoints * 10) / 10;
      return { ...stat, rawNetAdj, netAdj, rawTotalPoints, totalPoints };
    });

    this.leaderboard.sort((a, b) =>
      b.totalPoints - a.totalPoints ||
      b.rawNetAdj - a.rawNetAdj ||
      b.wins - a.wins ||
      (b.role2Wins + b.role4Wins) - (a.role2Wins + a.role4Wins) ||
      b.firstBloods - a.firstBloods ||
      0
    );

    this.leaderboard.forEach((s, i) => s.place = i + 1);
  }
}
