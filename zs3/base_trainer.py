from tqdm import tqdm
import torch

class BaseTrainer:
    def training(self, epoch):
        train_loss = 0.0
        self.model.train()
        tbar = tqdm(self.train_loader)
        num_img_tr = len(self.train_loader)
        for i, sample in enumerate(tbar):
#             print('sample', sample.keys())
#             print(sample["image"].size(), sample["label"].size(), sample["image_name"])
#             print('sample', sample[0].size(), sample[1].size())
#             if len(sample["image"]) > 1:
            if len(sample[0]) > 1:
#                 image, target = sample["image"], sample["label"]
                torch.set_printoptions(profile="full")
                image, target = sample[0], sample[1]
#                 target += 1
#                 print('=====================================================')
#                 print('target', target[0, 100:105, 100:120])
#                 mask = target == 256
#                 target[mask] = 0
#                 print('target', target[0, 100:105, 100:120])
#                 print('=====================================================')
#                 print('image', image.size(), image[:, 0, 100:105, 100:120])
#                 print('-----------------------------------------------------')
#                 print('target', target.size(), target[:, 100:105])
#                 print('=====================================================')
                if self.args.cuda:
                    image, target = image.cuda(), target.cuda()
                self.scheduler(self.optimizer, i, epoch, self.best_pred)
                self.optimizer.zero_grad()
                output = self.model(image)
                loss = self.criterion(output, target)
                loss.backward()
                self.optimizer.step()
                train_loss += loss.item()
                tbar.set_description("Train loss: %.3f" % (train_loss / (i + 1)))
                self.writer.add_scalar(
                    "train/total_loss_iter", loss.item(), i + num_img_tr * epoch
                )

                # Show 10 * 3 inference results each epoch
                if i % (num_img_tr // 10) == 0:
                    global_step = i + num_img_tr * epoch
                    self.summary.visualize_image(
                        self.writer,
                        self.args.dataset,
                        image,
                        target,
                        output,
                        global_step,
                    )

        self.writer.add_scalar("train/total_loss_epoch", train_loss, epoch)
        print(
            "[Epoch: %d, numImages: %5d]"
            % (epoch, i * self.args.batch_size + image.data.shape[0])
        )
        print(f"Loss: {train_loss:.3f}")

        if self.args.no_val:
            # save checkpoint every epoch
            is_best = False
            self.saver.save_checkpoint(
                {
                    "epoch": epoch + 1,
                    "state_dict": self.model.module.state_dict(),
                    "optimizer": self.optimizer.state_dict(),
                    "best_pred": self.best_pred,
                },
                is_best,
            )
