type PlausibleWindow = Window & {
  plausible?: (event: string, options?: { props?: Record<string, string | number> }) => void;
};

export const analytics = {
  track(event: string, props?: Record<string, string | number>): void {
    const w = window as PlausibleWindow;
    if (typeof w.plausible === 'function') {
      w.plausible(event, { props });
    }
  },
};
