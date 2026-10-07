import { ComponentModelBase } from "@vertigis/web/models";

export default class ClockModel extends ComponentModelBase {
    protected override async _onInitialize(): Promise<void> {
        this.start();
        await super._onInitialize();
    }
}
