import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function Register() {
  return (
    <div className="w-full h-screen flex flex-col">
      {/* Back Button */}
      <Link to="/" className="flex items-center gap-3 m-4 md:m-6">
        <ArrowLeft />
        <p className="text-base md:text-lg">Go Back Home</p>
      </Link>

      {/* Main Content */}
      <div className="w-full flex py-8 items-center justify-center">
        FORM OF REGISTRATIONS
      </div>
    </div>
  );
}
