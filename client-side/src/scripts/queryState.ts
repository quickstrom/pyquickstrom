import { queryState } from "../queries";

// @ts-ignore
const [queries, done] = args;

try {
  done({ Right: queryState(queries) });
} catch (e) {
  done({ Left: e });
}
