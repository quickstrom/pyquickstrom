# TodoMVC Testing Notes

New bugs since [The TodoMVC Showdown](https://wickstrom.tech/programming/2020/07/02/the-todomvc-showdown-testing-with-webcheck.html):

* [Reagent](https://todomvc.com/examples/reagent/#/): 
    - Allows adding a blank TODO item
* [Dojo](https://todomvc.com/examples/dojo/)
    - "Toggle all" doesn't untoggle all items when in the "Completed"
      or "Active" filters (in Completed it circles the state of the
      first, in Active it toggles just the first one)
