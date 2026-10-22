import Link from "next/link";

const STEPS = [
  ["Maya shops two makers", "Add a piece from AnnesCraftworks and another shop, then pay with 4242 4242 4242 4242."],
  ["The order splits", "One payment becomes one sub-order per shop, each with its own tracking number."],
  ["Jess ships only her half", "Seller Central shows AnnesCraftworks orders. KeinMaker cannot open them."],
  ["Ava changes a rate", "Revising a commission rule closes the old version. Orders already placed keep the old fee."],
  ["Daniel and Lin sign a payout", "Jess can request PAY-06. She cannot approve it. Two different staff members must sign."],
];

export default function GuidePage() {
  return (
    <div className="wrap max-w-2xl space-y-6 py-10">
      <h1 className="serif text-5xl">Demo guide</h1>
      <ol className="space-y-4">
        {STEPS.map(([title, body], index) => (
          <li key={title} className="panel p-4">
            <p className="text-xs uppercase tracking-wide text-[#b8572a]">Step {index + 1}</p>
            <h2 className="text-xl">{title}</h2>
            <p className="text-[#6b6258]">{body}</p>
          </li>
        ))}
      </ol>
      <p>
        Sign in from the <Link href="/login">login page</Link>. The password for every demo account is <b>demo</b>.
        API reference is at <a href="/api/docs">/api/docs</a>.
      </p>
    </div>
  );
}
