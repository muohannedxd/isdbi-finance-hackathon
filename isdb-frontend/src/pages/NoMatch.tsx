import NoMatchImage from "@/assets/images/nomatch.png";
import { Button } from "@/components/ui/button";
import { HashLink } from "react-router-hash-link";

export default function NoMatch() {
  return (
    <div className="flex flex-col justify-center items-center gap-16 min-h-screen p-6">
      <img src={NoMatchImage} alt="no_match" />
      <p className="text-2xl md:text-4xl text-center">
        {" "}
        Sorry, we can not find the page you are looking for!{" "}
      </p>
      <div className="flex gap-2">
        <HashLink rel="noreferrer noopener" to="/">
          <Button title="Return Home" />
        </HashLink>
      </div>
    </div>
  );
}
