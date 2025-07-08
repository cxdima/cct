import { Route } from '@angular/router';
import { LeaderboardComponent } from './pages/leaderboard/leaderboard.component';
import { NotFoundComponent } from "./pages/notFound/notFound.component";
import { AdminComponent } from "./pages/admin/admin.component";
import { GameComponent } from "./pages/game/game.component";

export const appRoutes: Route[] = [
  { path: '', redirectTo: '/game', pathMatch: 'full' },
  { path: 'game', component: GameComponent },
  { path: 'leaderboard', component: LeaderboardComponent },
  { path: 'admin', component: AdminComponent },
  { path: '**', component: NotFoundComponent }
];