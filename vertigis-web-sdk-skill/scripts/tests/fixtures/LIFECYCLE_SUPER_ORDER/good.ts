import { ComponentModelBase } from "@vertigis/web/models";

export default class ClockModel extends ComponentModelBase {
    protected override async _onInitialize(): Promise<void> {
        await super._onInitialize();
        this.start();
    }

    protected override async _onDestroy(): Promise<void> {
        this.stop();
        await super._onDestroy();
    }
}
