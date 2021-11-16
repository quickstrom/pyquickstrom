# TodoMVC Testing Notes

New bugs since [The TodoMVC Showdown](https://wickstrom.tech/programming/2020/07/02/the-todomvc-showdown-testing-with-webcheck.html):

* [Reagent](https://todomvc.com/examples/reagent/#/): 
    - Allows adding a blank TODO item
* [Dojo](https://todomvc.com/examples/dojo/)
    - "Toggle all" doesn't untoggle all items when in the "Completed"
      or "Active" filters (in Completed it circles the state of the
      first, in Active it toggles just the first one)
      
## Pending additions to the spec

- > The input element should be focused when the page is loaded, preferably by using the autofocus input attribute.


## Results (pending)

```
./run.py duel mithril react-alt angular2_es2015 binding-scala cujo elm jsblocks knockoutjs_require polymer vanilla-es6 angular-dart dijon emberjs firebase-angular js_of_ocaml kotlin-react ractive react-hooks typescript-angular vanillajs angularjs backbone_marionette canjs_require dojo emberjs_require gwt knockback lavaca_require react reagent typescript-backbone vue
```

- doesn't activate the edit input after double click
    - angular2 (failed)
- clears pending input on filter change
    - duel
    - mithril
- no checkboxes
    - angular2_es2015
- no filters
    - knockoutjs_require
    - dijon
- no `<strong>` in the todo count
    - vanilla-es6
- adding a new item first shows an empty state (not explictly forbidden by official spec)
    - angular-dart

