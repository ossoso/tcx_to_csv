# AUTO GENERATED FILE - DO NOT EDIT

myMyDashComponent <- function(id=NULL, label=NULL, value=NULL) {
    
    props <- list(id=id, label=label, value=value)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'MyDashComponent',
        namespace = 'my_dash_component',
        propNames = c('id', 'label', 'value'),
        package = 'myDashComponent'
        )

    structure(component, class = c('dash_component', 'list'))
}
