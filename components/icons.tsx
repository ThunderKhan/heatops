import type { SVGProps } from "react";

function Icon({ children, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const ThermometerIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0Z" />
    <path d="M12 9v7" />
  </Icon>
);
export const PinIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
    <circle cx="12" cy="10" r="2.5" />
  </Icon>
);
export const TrendIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="m4 16 5-5 4 4 7-8" />
    <path d="M15 7h5v5" />
  </Icon>
);
export const LayersIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="m12 3-9 5 9 5 9-5-9-5Z" />
    <path d="m3 12 9 5 9-5" />
    <path d="m3 16 9 5 9-5" />
  </Icon>
);
export const ArrowIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M5 12h14" />
    <path d="m14 7 5 5-5 5" />
  </Icon>
);
