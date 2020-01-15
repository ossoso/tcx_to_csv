const FORCE = { force: true }
const dragInGraph = (subject, fx_0, fy_0, fx_1, fy_1) => {
  const w = subject.width()
  const h = subject.height()
  cy.wrap(subject)
    .trigger('mousemove', (w * fx_0), (h * fy_0) )
    .trigger('mousedown', { which: 1 })
    .trigger('mousemove',  (w * fx_1), (h * fy_1), { ...FORCE, which: 1 })
    .trigger('mouseup', { ...FORCE })
}

const selectFromDropdown = (subject, value=null, index=null) => {
  cy.wrap(subject)
    .click()
    .get('div.Select-menu-outer')
    .get('div.VirtualizedSelectOption')
    .as('options')

  if ( Number.isInteger(index) && index >= 0 ) {
    cy.get('@options').eq(index).click()
    return
  }
  cy.get('@options').each(($opt) => {
    if (cy.wrap($opt).invoke('text') == value) {
      cy.wrap($opt).click()
      return
    }
  })
  console.error(`cannot find matching option using value=${value} or index=${index}`)
}

Cypress.Commands.add("dragHere", { prevSubject: 'element' }, dragInGraph)
Cypress.Commands.add("click_at_coord_fractions", { prevSubject: 'element' }, dragInGraph)
Cypress.Commands.add("selectInDropdown", { prevSubject: 'element' }, selectFromDropdown)
Cypress.Commands.add("selectDccDropdown", { prevSubject: 'element' }, selectFromDropdown)

// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })
