import { queryState } from "../queries";

// @ts-ignore
const [queries, done] = args;

done(queryState(queries));
