import { Button } from "@suite/design-system";

interface Props {
  value: number;
  onChange: (v: number) => void;
}

// Controllo quantità: due Button condivisi (@suite) attorno al valore.
export function QtyStepper({ value, onChange }: Props) {
  const sq = "h-7 w-7 p-0 text-base font-bold active:scale-90";
  return (
    <div className="flex items-center gap-2" onClick={(e) => e.preventDefault()}>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        className={sq}
        onClick={() => onChange(value - 1)}
        aria-label="Meno"
      >
        −
      </Button>
      <span className="w-6 text-center text-sm font-bold tabular-nums">
        {value}
      </span>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        className={sq}
        onClick={() => onChange(value + 1)}
        aria-label="Più"
      >
        +
      </Button>
    </div>
  );
}
