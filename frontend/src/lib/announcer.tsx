import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

const AnnouncerContext = createContext<(message: string) => void>(
  () => undefined,
);

export function AnnouncerProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  const announce = useCallback(
    (nextMessage: string) => setMessage(nextMessage),
    [],
  );

  return (
    <AnnouncerContext.Provider value={announce}>
      {children}
      <div aria-live="polite" className="sr-only">
        {message}
      </div>
    </AnnouncerContext.Provider>
  );
}

export function useAnnounce() {
  return useContext(AnnouncerContext);
}
