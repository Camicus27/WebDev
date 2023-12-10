import { $ } from "/static/jquery/src/jquery.js";

export function say_hi(elt) {
    console.log("Say hi to", elt);
}

say_hi($("h1"));