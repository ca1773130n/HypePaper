import { StreamlitComponentBase, with  Streamlit } from "streamlit-component-lib";
import React, { ReactNode } from "react";

interface State {
  value: string | null;
}

class StCookieManager extends StreamlitComponentBase<State> {
  public state: State = {
    value: this.props.args["default"],
  };

  public componentDidMount() {
    if (this.props.args["expires"] === 0) {
      this.deleteCookie();
    } else if (this.props.args["value"] !== undefined && this.props.args["value"] !== null) {
      this.setCookie();
    } else {
      this.getCookie();
    }
  }

  public componentDidUpdate() {
    if (this.props.args["expires"] === 0) {
      this.deleteCookie();
    } else if (this.props.args["value"] !== undefined && this.props.args["value"] !== null) {
      this.setCookie();
    } else if (this.props.args["name"] && this.state.value === null) { // Only get if value is null
      this.getCookie();
    }
  }

  private setCookie = () => {
    const { name, value, expires } = this.props.args;
    const date = new Date();
    date.setDate(date.getDate() + expires);
    document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/`;
    this.setState({ value });
    Streamlit.setComponentValue(value);
  };

  private getCookie = () => {
    const { name } = this.props.args;
    const cookieName = `${name}=`;
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(cookieName) === 0) {
        const value = c.substring(cookieName.length, c.length);
        this.setState({ value });
        Streamlit.setComponentValue(value);
        return;
      }
    }
    this.setState({ value: null });
    Streamlit.setComponentValue(null);
  };

  private deleteCookie = () => {
    const { name } = this.props.args;
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
    this.setState({ value: null });
    Streamlit.setComponentValue(null);
  };

  public render = (): ReactNode => {
    return null;
  };
}

export default withStreamlit(StCookieManager); 