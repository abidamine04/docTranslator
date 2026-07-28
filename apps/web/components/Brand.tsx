import { Languages } from "lucide-react";

export function Brand() {
  return (
    <div className="brand">
      <span className="brand-mark"><Languages size={18} /></span>
      <span>DocTranslator</span>
      <span className="beta">SELF-HOSTED</span>
    </div>
  );
}

