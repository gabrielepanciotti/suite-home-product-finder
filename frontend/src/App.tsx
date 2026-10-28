import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AppShell,
  Button,
  EmptyState,
  Skeleton,
  VistaProvider,
  useVista,
} from "@suite/design-system";
import { Catalogo } from "./components/Catalogo";
import { Contenere } from "./components/Contenere";
import { Spazi } from "./components/Spazi";
import { SectionIcon } from "./components/SectionIcon";
import { AnnouncerProvider } from "./lib/announcer";
import { Cerca } from "./pages/Cerca";
import { Impostazioni } from "./pages/Impostazioni";
import { Risultati } from "./pages/Risultati";
import { Salvati } from "./pages/Salvati";
import { vistaFetcher } from "./lib/vista";

const PAGE_IDS = new Set([
  "cerca",
  "risultati",
  "salvati",
  "spazi",
  "contenere",
  "catalogo",
  "impostazioni",
]);
const DEFAULT_SIDEBAR_COLLAPSED =
  typeof window !== "undefined" &&
  window.matchMedia("(max-width: 767px)").matches;

interface HashRoute {
  section: string;
  slug?: string;
}

function leggiHash(): HashRoute {
  const [section = "", rawSlug] = window.location.hash.slice(1).split("/");
  return {
    section: PAGE_IDS.has(section) ? section : "cerca",
    slug: rawSlug ? decodeURIComponent(rawSlug) : undefined,
  };
}

function vai(section: string) {
  window.location.hash = section;
}

function ShellLoading() {
  return (
    <AppShell defaultCollapsed>
      <AppShell.Sidebar>
        {Array.from({ length: 6 }, (_, index) => (
          <Skeleton key={index} className="h-10 w-full" />
        ))}
      </AppShell.Sidebar>
      <div className="flex min-w-0 flex-1 flex-col">
        <AppShell.Topbar>
          <Skeleton className="h-4 w-40" />
        </AppShell.Topbar>
        <AppShell.Content className="max-md:pl-12 p-4 sm:p-6">
          <div className="space-y-4">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </AppShell.Content>
      </div>
    </AppShell>
  );
}

function HomeProductFinderShell() {
  const { sezioniVisibili, stato, etichetta, ricarica } = useVista();
  const [route, setRoute] = useState<HashRoute>(leggiHash);

  useEffect(() => {
    const sync = () => setRoute(leggiHash());
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  const visibleIds = useMemo(
    () => new Set(sezioniVisibili.map(({ id }) => id)),
    [sezioniVisibili],
  );
  const active = visibleIds.has(route.section)
    ? route.section
    : (sezioniVisibili[0]?.id ?? "cerca");

  useEffect(() => {
    const current = window.location.hash.slice(1);
    if (!current || !PAGE_IDS.has(current.split("/")[0])) vai("cerca");
  }, []);

  if (stato === "loading") return <ShellLoading />;

  if (stato === "error") {
    return (
      <AppShell defaultCollapsed>
        <AppShell.Content className="grid place-items-center p-4">
          <EmptyState
            icon={<SectionIcon id="errore" />}
            title="Impossibile caricare la vista"
            description="La configurazione della navigazione non è disponibile."
            action={<Button onClick={() => void ricarica()}>Riprova</Button>}
          />
        </AppShell.Content>
      </AppShell>
    );
  }

  const settings = sezioniVisibili.find(({ id }) => id === "impostazioni");
  const navigation = sezioniVisibili
    .filter(({ id }) => id !== "impostazioni")
    .slice(0, 6);

  let page: ReactNode;
  switch (active) {
    case "risultati":
      page = <Risultati slug={route.slug} />;
      break;
    case "salvati":
      page = <Salvati />;
      break;
    case "spazi":
      page = <Spazi />;
      break;
    case "contenere":
      page = <Contenere />;
      break;
    case "catalogo":
      page = <Catalogo />;
      break;
    case "impostazioni":
      page = <Impostazioni />;
      break;
    default:
      page = <Cerca />;
  }

  return (
    <AppShell
      defaultCollapsed={DEFAULT_SIDEBAR_COLLAPSED}
    >
      <AppShell.Sidebar
        settingsItem={
          settings ? (
            <AppShell.Sidebar.Item
              icon={<SectionIcon id={settings.id} />}
              label={settings.titolo}
              active={active === settings.id}
              onClick={() => vai(settings.id)}
            />
          ) : undefined
        }
      >
        {navigation.map((item) => (
          <AppShell.Sidebar.Item
            key={item.id}
            icon={<SectionIcon id={item.id} />}
            label={item.titolo}
            active={active === item.id}
            onClick={() => vai(item.id)}
          />
        ))}
      </AppShell.Sidebar>
      <div className="flex min-w-0 flex-1 flex-col">
        <AppShell.Topbar>
          <span className="truncate text-sm font-medium text-text">
            HomeProductFinder
          </span>
          <span className="truncate text-xs text-muted">{etichetta}</span>
        </AppShell.Topbar>
        <AppShell.Content className="max-md:pl-12 p-4 sm:p-6">
          {page}
        </AppShell.Content>
      </div>
    </AppShell>
  );
}

export default function App() {
  return (
    <AnnouncerProvider>
      <VistaProvider fetcher={vistaFetcher}>
        <HomeProductFinderShell />
      </VistaProvider>
    </AnnouncerProvider>
  );
}
