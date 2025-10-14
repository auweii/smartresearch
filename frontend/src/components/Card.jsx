// basic card container — keeps consistent rounded shadow style
export default function Card({ className = "", children }) {
  return <div className={`card ${className}`}>{children}</div>;
}
