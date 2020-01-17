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

describe('Uploading data', () => {
  beforeEach(() => {
    cy.visit('localhost:8050')
  })

  it('upload dcc visible', () => {
    cy.get('#data-upload')
  })

  it('file uploaded', () => {
    uploadTestFile(testFname)
  });

  describe('Validating conversion results of single recording', () => {
    // https://on.cypress.io/interacting-with-elements
    beforeEach(() => {
      uploadTestFile(testFname)
    })


    it('one dataframe stored', () => {
      cy.get('#activities-json').should((jsonDiv) => {
        const text = jsonDiv.text()
        const serializedData = JSON.parse(text)
        expect(Object.keys(serializedData)).to.have.length(1)
      })
    });

    describe('dropdown tests', () => {
      beforeEach(() => {
        cy.get('#loaded-dataframes').as('dropdown')
        cy.get("@dropdown").click()
      })


      it('dropdown appears with 1 item', () => {
        cy.get("@dropdown").get('div.Select-menu-outer').should(($menu) => {
          expect($menu.text().split('\n')).to.have.length(1)
        })
      })

      it.only('selected options stored in \'activity-ids\'', () => {
        cy.get("@dropdown").get('div.Select-menu-outer').then($menu => {
          cy.get('#activity-ids').should(($ids) => {
            const idL = JSON.parse($ids.text())
            expect($menu.text().split('\n')).to.deep.equal(idL)
          })
        })
      })
    })
  }
          )
})
