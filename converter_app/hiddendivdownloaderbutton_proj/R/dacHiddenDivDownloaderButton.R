# AUTO GENERATED FILE - DO NOT EDIT

dacHiddenDivDownloaderButton <- function(id=NULL, label=NULL, filename=NULL, hiddenDivData=NULL) {
    
    props <- list(id=id, label=label, filename=filename, hiddenDivData=hiddenDivData)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'HiddenDivDownloaderButton',
        namespace = 'hiddendivdownloaderbutton',
        propNames = c('id', 'label', 'filename', 'hiddenDivData'),
        package = 'hiddendivdownloaderbutton'
        )

    structure(component, class = c('dash_component', 'list'))
}
