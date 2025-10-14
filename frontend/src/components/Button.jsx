// simple reusable button — matches Tailwind utility classes
export default function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}) {
  const base = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "btn-ghost",
  }[variant];

  return (
    <button {...props} className={`${base} ${className}`}>
      {children}
    </button>
  );
}
