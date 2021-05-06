import { toArray } from "./arrays";
import { getPosition, Position } from "./position";
import { isElementVisible } from "./visibility";

export type Selector = string;

export interface Schema {
    [k: string]: Schema,
};

export interface Dependencies {
    [selector: string]: Schema,
};

export type Value = string | number | boolean | Element | null;

interface ElementState {
    ref?: Element,
    position?: Position,
    [x: string]: any,
}

export interface QueriedState {
    [selector: string]: Array<ElementState>;
}

export function runQuery(selector: Selector, schema: Schema): ElementState[] {
    function queryCssValues(element: Element, subSchema: Schema): any {
        const css = {};
        Object.entries(subSchema).forEach(([name, subSchema]) => {
            if (subSchema !== {}) {
                throw Error("Schema for CSS value cannot contain sub-schemas.");
            } else {
                return window
                    .getComputedStyle(element)
                    .getPropertyValue(name);
            }
        });
        return css;
    }

    const elements = toArray(document.querySelectorAll(selector)) as Element[];
    return elements.map((element) => {
        var m: ElementState = {};
        Object.entries(schema).forEach(([key, subSchema]) => {
            switch (key) {
                case "ref":
                    m.ref = element;
                    break;
                case "enabled":
                    // @ts-ignore
                    m[key] = !element.disabled;
                    break;
                case "visible":
                    m[key] = isElementVisible(element as HTMLElement);
                    break;
                case "active":
                    m[key] = document.activeElement == element;
                    break;
                case "classList":
                    // @ts-ignore
                    m[key] = Array(...element.classList);
                    break;
                case "css":
                    m[key] = queryCssValues(element, subSchema);
                    break;
                default:
                    // @ts-ignore
                    m[key] = element[key];
                    break;
            }
        });
        m.position = getPosition(element);
        return m;
    });
}

export function queryState(deps: Dependencies): QueriedState {
    var r: QueriedState = {};
    Object.entries(deps).forEach(([selector, schema]) => {
        r[selector] = runQuery(selector, schema);
    });
    return r;
}
