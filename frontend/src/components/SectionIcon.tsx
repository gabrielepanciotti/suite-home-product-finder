import {
  Boxes,
  CircleAlert,
  ListFilter,
  Package,
  Ruler,
  Search,
  Settings,
  Star,
  type LucideIcon,
} from "lucide-react";

const sectionIcons: Record<string, LucideIcon> = {
  cerca: Search,
  risultati: ListFilter,
  salvati: Star,
  spazi: Ruler,
  contenere: Package,
  catalogo: Boxes,
  impostazioni: Settings,
  errore: CircleAlert,
};

export function SectionIcon({ id }: { id: string }) {
  const Icon = sectionIcons[id] ?? CircleAlert;

  return <Icon aria-hidden="true" />;
}
