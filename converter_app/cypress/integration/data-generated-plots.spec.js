/// <reference types="Cypress" />

describe('Test  interactivity of graphs 1 and 2 ', () => {
  beforeEach(() => {
    cy.visit('localhost:8050')
  })

  it('graph 1 visible', () => {
    cy.get('#graph-1').should('have.css', 'display', 'none')
// (($g1) => {
//       expect($g1).dom.not.to.be.displayed()
//     })
  })

})
