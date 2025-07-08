import {
  Component,
  AfterViewInit,
  OnDestroy,
  ElementRef,
  ViewChild,
  HostListener,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import * as L from 'leaflet';

// raw import of your JSON coords
import rawLocations from 'public/locations.json';
import { RouterOutlet } from "@angular/router";

interface Loc {
  id: string;
  coord: [number, number];
}

// force the tuple type
const pixelLocations: Loc[] = (rawLocations as Array<{ id: string; coord: number[] }>).map(l => ({
  id:    l.id,
  coord: [l.coord[0], l.coord[1]],
}));

interface APINode {
  id:       number;
  occupied: boolean;
  team:     number | null;
}

@Component({
  selector: 'app-game',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './game.component.html',
  styleUrl: './game.component.css',
})

export class GameComponent implements AfterViewInit, OnDestroy {
  @ViewChild('mapContainer', { static: true })
  mapContainer!: ElementRef<HTMLDivElement>;

  private map!: L.Map;
  private imageOverlay!: L.ImageOverlay;
  private occupantOverlays = new Map<string, L.ImageOverlay>();

  /** Capture-mode */
  capturing = false;
  captured: Loc[] = [];

  canZoomIn = false;
  canZoomOut = false;

  /** Map image + pixel dimensions */
  private readonly IMAGE_URL = 'numbers.jpg';
  private readonly IMAGE_SIZE: [number, number] = [5625, 10000];

  /** Zoom step */
  private readonly ZOOM_STEP = 0.4;

  constructor(private http: HttpClient) {}

  ngAfterViewInit() {
    this.initMap();
    this.hookManualZoom();
    this.loadGameLocations();
  }

  ngOnDestroy() {
    this.map?.remove();
  }

  @HostListener('window:resize')
  onResize() {
    if (this.map) this.fitWidth();
  }

  toggleCapture() {
    this.capturing = !this.capturing;
  }

  private initMap() {
    // build map with built-in zooms off
    this.map = L.map(this.mapContainer.nativeElement, {
      crs: L.CRS.Simple,
      zoomControl: false,
      attributionControl: false,
      minZoom: -5,
      maxZoom: 5,
      scrollWheelZoom: false,
      touchZoom: false,
      doubleClickZoom: false,
      zoomSnap: this.ZOOM_STEP,
      zoomDelta: this.ZOOM_STEP,
      wheelDebounceTime: 0,
      wheelPxPerZoomLevel: 6,
      zoomAnimation: false,
      inertia: false,
      bounceAtZoomLimits: false,
      maxBoundsViscosity: 1,
    });

    // overlay map image
    const bounds = L.latLngBounds([0, 0], this.IMAGE_SIZE);
    this.imageOverlay = L.imageOverlay(this.IMAGE_URL, bounds).addTo(this.map);
    this.map.setMaxBounds(bounds);

    // capture-mode click recording
    this.map.on('click', (ev) => {
      if (!this.capturing) return;
      const { lat, lng } = ev.latlng;
      const id = `loc_${this.captured.length}`;
      L.circleMarker(ev.latlng, { radius: 6, color: 'red' })
        .addTo(this.map)
        .bindTooltip(id)
        .openTooltip();
      this.captured.push({ id, coord: [Math.round(lng), Math.round(lat)] });
    });

    // enforce bounds + update buttons on every view change
    this.map.on('moveend zoomend', () => {
      this.enforceBounds();
      this.updateZoomState();
    });

    // initial fit & lock
    this.fitWidth();
  }

  /** FULL-WIDTH & CENTER on init, lock as minZoom */
  private fitWidth() {
    const bounds = this.imageOverlay.getBounds();
    const w = this.mapContainer.nativeElement.clientWidth;
    let z = Math.log2(w / this.IMAGE_SIZE[1]);
    z = Math.max(this.map.getMinZoom(), Math.min(this.map.getMaxZoom(), z));

    // lock out any further zoom out
    this.map.setMinZoom(z);

    // **CENTER** the map on the image center at that zoom
    this.map.setView(bounds.getCenter(), z, { animate: false });
    this.updateZoomState();
  }

  /** never let whitespace appear */
  private enforceBounds() {
    // clamp zoom
    const z = this.map.getZoom();
    const min = this.map.getMinZoom();
    if (z < min) {
      this.map.setZoom(min, { animate: false });
      return;
    }
    // clamp pan inside image
    const ib = this.imageOverlay.getBounds();
    const vb = this.map.getBounds();
    if (!ib.contains(vb)) {
      this.map.panInsideBounds(ib, { animate: false });
    }
  }

  private updateZoomState() {
    const z = this.map.getZoom();
    this.canZoomIn = z < this.map.getMaxZoom();
    this.canZoomOut = z > this.map.getMinZoom();
  }

  /** ± buttons */
  zoomIn() {
    if (this.canZoomIn) this.manualZoom(this.ZOOM_STEP);
  }
  zoomOut() {
    if (this.canZoomOut) this.manualZoom(-this.ZOOM_STEP);
  }

  /** manual wheel/pinch & dblclick → manualZoom */
  private hookManualZoom() {
    const el = this.mapContainer.nativeElement as HTMLElement;

    el.addEventListener(
      'wheel',
      (e: WheelEvent) => {
        e.preventDefault();
        const d = e.deltaY < 0 ? this.ZOOM_STEP : -this.ZOOM_STEP;
        this.manualZoom(d);
      },
      { passive: false }
    );

    el.addEventListener('dblclick', (e) => {
      e.preventDefault();
      this.manualZoom(this.ZOOM_STEP);
    });
  }

  /** instant setZoom + clamp pan */
  private manualZoom(delta: number) {
    let z = this.map.getZoom() + delta;
    z = Math.max(this.map.getMinZoom(), Math.min(this.map.getMaxZoom(), z));
    this.map.setZoom(z, { animate: false });
    this.map.panInsideBounds(this.imageOverlay.getBounds(), { animate: false });
  }

  /** fetch & draw occupied nodes */
  private loadGameLocations() {
    this.http
      .get<APINode[]>(
        'https://swasunehdia2ytb5vzz3gp6ed40oglee.lambda-url.us-east-1.on.aws/locations'
      )
      .subscribe((nodes) => {
        nodes.forEach((node) => {
          if (!node.occupied) return;
          const loc = pixelLocations.find((l) => l.id === `loc_${node.id}`);
          if (!loc) return;
          this.placeOccupantOverlay(
            `loc_${node.id}`,
            loc.coord[0],
            loc.coord[1],
            `teams/team-${node.team}.png`
          );
        });
      });
  }

  /** places or moves an overlay-icon that scales with zoom */
  private placeOccupantOverlay(id: string, x: number, y: number, url: string) {
    const old = this.occupantOverlays.get(id);
    if (old) old.remove();
    const size = 50,
      half = size / 2;
    const sw: L.LatLngExpression = [y - half, x - half];
    const ne: L.LatLngExpression = [y + half, x + half];
    const b = L.latLngBounds(sw, ne);
    const ov = L.imageOverlay(url, b, { interactive: false }).addTo(this.map);
    this.occupantOverlays.set(id, ov);
  }
}
