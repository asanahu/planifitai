import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}
interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
    this.retry = this.retry.bind(this);
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  retry() {
    this.setState({ hasError: false });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-center">
          <p className="mb-2">Algo salió mal.</p>
          <button
            onClick={this.retry}
            className="rounded bg-blue-500 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Reintentar"
          >
            Reintentar
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
