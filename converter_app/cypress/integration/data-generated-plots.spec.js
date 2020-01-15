/// <reference types="Cypress" />
import 'cypress-file-upload'

const testFname = 'test_cycling_data.tcx'
const uploadTestFile = (fileContent) => {
  cy.fixture(testFname).then(fileContent => {
    cy.get('#data-upload > .data-upload > input').upload(
      { fileContent, fileName: testFname, mimeType: 'text/xml',
        encoding: 'ascii' },
      { 
        // subjectType: 'drag-n-drop',
        force: true },
    );
  });
}

describe('Test  interactivity of graphs 1 and 2 ', () => {
  beforeEach(() => {
    cy.visit('localhost:8050')
  })

  it('graphs initially hidden', () => {
    cy.get('#graphing-container').should('have.css', 'display', 'none')
  })

  describe('Plotting of stored data', () => {
    beforeEach(() => {
      uploadTestFile(testFname)
      cy.get('#loaded-dataframes').selectInDropdown(null, 0)
    })
    it.only('select segment of graph-1 by drag-n-drop', () => {
      cy.get('#graph-1', { timeout: 30000 })
        .should('be.visible')
        .dragHere(0.2, 0.5, 0.6, 0.4)
    })
  })

  })
